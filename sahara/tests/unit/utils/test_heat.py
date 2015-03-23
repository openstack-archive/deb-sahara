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

import mock
import testtools

from sahara import exceptions as ex
from sahara.utils.openstack import heat as h


class TestClusterStack(testtools.TestCase):
    @mock.patch("sahara.context.sleep", return_value=None)
    def test_wait_completion(self, _):
        stack = FakeHeatStack('CREATE_IN_PROGRESS', 'CREATE_COMPLETE')
        h.wait_stack_completion(stack)

        stack = FakeHeatStack('UPDATE_IN_PROGRESS', 'UPDATE_COMPLETE')
        h.wait_stack_completion(stack)

        stack = FakeHeatStack('DELETE_IN_PROGRESS', 'DELETE_COMPLETE')
        h.wait_stack_completion(stack)

        stack = FakeHeatStack('CREATE_IN_PROGRESS', 'CREATE_FAILED')
        with testtools.ExpectedException(
                ex.HeatStackException,
                value_re=("Heat stack failed with status "
                          "CREATE_FAILED\nError ID: .*")):
            h.wait_stack_completion(stack)


class FakeHeatStack(object):
    def __init__(self, stack_status=None, new_status=None, stack_name=None):
        self.stack_status = stack_status or ''
        self.new_status = new_status or ''
        self.stack_name = stack_name or ''

    def get(self):
        self.stack_status = self.new_status

    @property
    def status(self):
        s = self.stack_status
        return s[s.index('_') + 1:]
