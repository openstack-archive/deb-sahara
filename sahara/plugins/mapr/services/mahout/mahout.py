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


MAHOUT = np.NodeProcess(
    name='mahout',
    ui_name='Mahout',
    package='mapr-mahout',
    open_ports=[]
)


@six.add_metaclass(s.Single)
class Mahout(s.Service):
    def __init__(self):
        super(Mahout, self).__init__()
        self._name = 'mahout'
        self._ui_name = 'Mahout'
        self._version = '0.9'
        self._node_processes = [MAHOUT]
        self._validation_rules = [vu.at_least(1, MAHOUT)]
