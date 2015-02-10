# Copyright (c) 2013 Mirantis Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import pickle
import sys

from eventlet.green import subprocess
from eventlet import timeout as e_timeout
from oslo_log import log as logging

from sahara import context

LOG = logging.getLogger(__name__)


def _get_sub_executable():
    return '%s/_sahara-subprocess' % os.path.dirname(sys.argv[0])


def start_subprocess():
    return subprocess.Popen((sys.executable, _get_sub_executable()),
                            close_fds=True,
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)


def run_in_subprocess(proc, func, args=(), kwargs={}, interactive=False):
    try:
        pickle.dump(func, proc.stdin)
        pickle.dump(args, proc.stdin)
        pickle.dump(kwargs, proc.stdin)
        proc.stdin.flush()

        if not interactive:
            result = pickle.load(proc.stdout)

            if 'exception' in result:
                raise SubprocessException(result['exception'])

            return result['output']
    finally:
        # NOTE(dmitryme): in openstack/common/processutils.py it
        # is suggested to sleep a little between calls to multiprocessing.
        # That should allow it make some necessary cleanup
        context.sleep(0)


def _finish(cleanup_func):
    cleanup_func()
    sys.stdin.close()
    sys.stdout.close()
    sys.stderr.close()
    sys.exit(0)


def shutdown_subprocess(proc, cleanup_func):
    try:
        with e_timeout.Timeout(5):
            # timeout would mean that our single-threaded subprocess
            # is hung on previous task which blocks _finish to complete
            run_in_subprocess(proc, _finish, (cleanup_func,))
    except BaseException:
        # exception could be caused by either timeout, or
        # successful shutdown, ignoring anyway
        pass
    finally:
        kill_subprocess(proc)


def kill_subprocess(proc):
    proc.stdin.close()
    proc.stdout.close()
    proc.stderr.close()

    try:
        proc.kill()
    except OSError:
        # could be caused by process already dead, so ignoring
        pass


class SubprocessException(Exception):
    def __init__(self, e):
        super(SubprocessException, self).__init__(e)
