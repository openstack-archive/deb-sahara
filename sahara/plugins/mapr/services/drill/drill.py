# Copyright (c) 2015, MapR Technologies
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


import six

import sahara.plugins.mapr.domain.node_process as np
import sahara.plugins.mapr.domain.service as s
import sahara.plugins.mapr.util.commands as cmd
import sahara.plugins.mapr.util.validation_utils as vu


DRILL = np.NodeProcess(
    name='drill-bits',
    ui_name='Drill',
    package='mapr-drill',
    open_ports=[]
)


@six.add_metaclass(s.Single)
class Drill(s.Service):
    def __init__(self):
        super(Drill, self).__init__()
        self._name = 'drill'
        self._ui_name = 'Drill'
        self._version = '0.7'
        self._node_processes = [DRILL]
        self._ui_info = [('Drill', DRILL, 'http://%s:8047')]
        self._validation_rules = [vu.at_least(1, DRILL)]

    def install(self, cluster_context, instances):
        # Drill requires running cluster
        pass

    def post_start(self, cluster_context, instances):
        instances = instances or cluster_context.get_instances(DRILL)
        super(Drill, self).install(cluster_context, instances)
        for instance in instances:
            cmd.chown(instance, 'mapr:mapr', self.service_dir(cluster_context))
            cmd.re_configure_sh(instance, cluster_context)
