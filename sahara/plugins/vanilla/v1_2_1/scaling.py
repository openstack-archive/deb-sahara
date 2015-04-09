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

import six

from sahara import context
from sahara.i18n import _
from sahara.plugins import utils
from sahara.plugins.vanilla.v1_2_1 import config_helper
from sahara.plugins.vanilla.v1_2_1 import run_scripts as run
from sahara.utils import cluster_progress_ops as cpo
from sahara.utils import poll_utils
from sahara.utils import remote


@cpo.event_wrapper(True, step=_("Decommission %s") % "TaskTrackers")
def decommission_tt(jt, inst_to_be_deleted, survived_inst):
    with remote.get_remote(jt) as r:
        r.write_file_to('/etc/hadoop/tt.excl',
                        utils.generate_fqdn_host_names(
                            inst_to_be_deleted))
        run.refresh_nodes(remote.get_remote(jt), "mradmin")
        context.sleep(3)
        r.write_files_to({'/etc/hadoop/tt.incl':
                         utils.generate_fqdn_host_names(survived_inst),
                         '/etc/hadoop/tt.excl': "",
                          })


def is_decommissioned(r, inst_to_be_deleted):
    cmd = r.execute_command("sudo su -c 'hadoop dfsadmin -report' hadoop")
    datanodes_info = parse_dfs_report(cmd[1])
    for inst in inst_to_be_deleted:
        for dn in datanodes_info:
            if (dn["Name"].startswith(inst.internal_ip)) and (
                    dn["Decommission Status"] != "Decommissioned"):
                return False
    return True


@cpo.event_wrapper(True, step=_("Decommission %s") % "DataNodes")
def decommission_dn(nn, inst_to_be_deleted, survived_inst):
    with remote.get_remote(nn) as r:
        r.write_file_to('/etc/hadoop/dn.excl',
                        utils.generate_fqdn_host_names(
                            inst_to_be_deleted))
        run.refresh_nodes(remote.get_remote(nn), "dfsadmin")
        context.sleep(3)

        poll_utils.plugin_option_poll(
            nn.cluster, is_decommissioned,
            config_helper.DECOMMISSIONING_TIMEOUT,
            _("Decommission %s") % "DataNodes", 3,
            {'r': r, 'inst_to_be_deleted': inst_to_be_deleted})

        r.write_files_to({'/etc/hadoop/dn.incl':
                          utils.generate_fqdn_host_names(survived_inst),
                          '/etc/hadoop/dn.excl': ""})


def parse_dfs_report(cmd_output):
    report = cmd_output.rstrip().split(os.linesep)
    array = []
    started = False
    for line in report:
        if started:
            array.append(line)
        if line.startswith("Datanodes available"):
            started = True

    res = []
    datanode_info = {}
    for i in six.moves.xrange(0, len(array)):
        if array[i]:
            idx = str.find(array[i], ':')
            name = array[i][0:idx]
            value = array[i][idx + 2:]
            datanode_info[name.strip()] = value.strip()
        if not array[i] and datanode_info:
            res.append(datanode_info)
            datanode_info = {}
    if datanode_info:
        res.append(datanode_info)
    return res
