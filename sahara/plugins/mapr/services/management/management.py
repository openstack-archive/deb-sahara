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
import sahara.plugins.mapr.util.validation_utils as vu


ZK_CLIENT_PORT = 5181

ZOOKEEPER = np.NodeProcess(
    name='mapr-zookeeper',
    ui_name='ZooKeeper',
    package='mapr-zookeeper',
    open_ports=[ZK_CLIENT_PORT]
)

WEB_SERVER = np.NodeProcess(
    name='webserver',
    ui_name='Webserver',
    package='mapr-webserver',
    open_ports=[8443]
)

METRICS = np.NodeProcess(
    name='metrics',
    ui_name='Metrics',
    package='mapr-metrics',
    open_ports=[1111]
)


@six.add_metaclass(s.Single)
class Management(s.Service):
    def __init__(self):
        super(Management, self).__init__()
        self._ui_name = 'Management'
        self._node_processes = [ZOOKEEPER, WEB_SERVER, METRICS]
        self._ui_info = [
            ('MapR Control System (MCS)', WEB_SERVER, 'https://%s:8443'),
        ]
        self._validation_rules = [
            vu.at_least(1, ZOOKEEPER),
            vu.exactly(1, WEB_SERVER),
            vu.odd_count_of(ZOOKEEPER),
        ]
