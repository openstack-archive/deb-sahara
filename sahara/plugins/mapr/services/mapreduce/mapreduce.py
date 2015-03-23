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

import sahara.plugins.mapr.domain.configuration_file as bcf
import sahara.plugins.mapr.domain.node_process as np
import sahara.plugins.mapr.domain.service as s
import sahara.plugins.mapr.util.validation_utils as vu
from sahara.plugins.mapr.versions import version_handler_factory as vhf
from sahara.swift import swift_helper
from sahara.topology import topology_helper as topo
from sahara.utils import files as f

JOB_TRACKER = np.NodeProcess(
    name='jobtracker',
    ui_name='JobTracker',
    package='mapr-jobtracker',
    open_ports=[9001, 50030]
)
TASK_TRACKER = np.NodeProcess(
    name='tasktracker',
    ui_name='TaskTracker',
    package='mapr-tasktracker',
    open_ports=[50060]
)

JACKSON_CORE_ASL = ('plugins/mapr/services/swift/resources/'
                    'jackson-core-asl-1.9.13.jar')
JACKSON_MAPPER_ASL = ('plugins/mapr/services/swift/resources/'
                      'jackson-mapper-asl-1.9.13.jar')


@six.add_metaclass(s.Single)
class MapReduce(s.Service):
    cluster_mode = 'classic'

    def __init__(self):
        super(MapReduce, self).__init__()
        self._ui_name = 'MapReduce'
        self._name = 'hadoop'
        self._version = '0.20.2'
        self._node_processes = [JOB_TRACKER, TASK_TRACKER]
        self._ui_info = [
            ('JobTracker', JOB_TRACKER, 'http://%s:50030'),
            ('TaskTracker', TASK_TRACKER, 'http://%s:50060'),
        ]
        self._validation_rules = [
            vu.at_least(1, JOB_TRACKER),
            vu.at_least(1, TASK_TRACKER),
        ]

    def _get_packages(self, node_processes):
        result = []

        result += self.dependencies
        result += [(np.package, None) for np in node_processes]

        return result

    # mapred-site.xml
    def get_config_files(self, cluster_context, configs, instance=None):
        core_site = bcf.HadoopXML("core-site.xml")
        core_site.remote_path = self.conf_dir(cluster_context)
        if instance:
            core_site.fetch(instance)
        core_site.add_properties(self._get_core_site_props(cluster_context))

        mapred_site = bcf.HadoopXML("mapred-site.xml")
        mapred_site.remote_path = self.conf_dir(cluster_context)
        if instance:
            mapred_site.fetch(instance)
        mapred_site.load_properties(configs)
        mapred_site.add_properties(
            self._get_mapred_site_props(cluster_context))

        return [core_site, mapred_site]

    def _get_core_site_props(self, context):
        result = {}
        if context.is_node_aware:
            for conf in topo.vm_awareness_core_config():
                result[conf['name']] = conf['value']
        for conf in swift_helper.get_swift_configs():
            result[conf['name']] = conf['value']
        for conf in self._get_impersonation_props():
            result[conf['name']] = conf['value']
        return result

    def _get_mapred_site_props(self, context):
        result = {}
        if context.is_node_aware:
            for conf in topo.vm_awareness_mapred_config():
                result[conf['name']] = conf['value']
        return result

    def _get_impersonation_props(self):
        return [
            {'name': 'hadoop.proxyuser.mapr.groups', 'value': '*'},
            {'name': 'hadoop.proxyuser.mapr.hosts', 'value': '*'}
        ]

    def configure(self, cluster_context, instances=None):
        version = cluster_context.cluster.hadoop_version
        handler = vhf.VersionHandlerFactory.get().get_handler(version)
        if handler._version == '3.1.1':
            self._update_jackson_libs(cluster_context, instances)

    def _update_jackson_libs(self, context, instances):
        hadoop_lib = context.hadoop_lib
        core_asl = f.get_file_text(JACKSON_CORE_ASL)
        mapper_asl = f.get_file_text(JACKSON_MAPPER_ASL)
        core_asl_path = '%s/%s' % (hadoop_lib, 'jackson-core-asl-1.9.13.jar')
        mapper_path = '%s/%s' % (hadoop_lib, 'jackson-mapper-asl-1.9.13.jar')
        libs = {
            core_asl_path: core_asl,
            mapper_path: mapper_asl
        }
        for instance in instances:
            with instance.remote() as r:
                r.execute_command('rm %s/jackson-*.jar' % hadoop_lib,
                                  run_as_root=True)
                r.write_files_to(libs, run_as_root=True)

    def get_file_path(self, file_name):
        template = 'plugins/mapr/services/mapreduce/resources/%s'
        return template % file_name
