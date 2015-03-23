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


from sahara import exceptions as ex
from sahara.i18n import _
from sahara.service import api
import sahara.service.validations.base as b


def check_node_group_template_create(data, **kwargs):
    b.check_node_group_template_unique_name(data['name'])
    b.check_plugin_name_exists(data['plugin_name'])
    b.check_plugin_supports_version(data['plugin_name'],
                                    data['hadoop_version'])
    b.check_node_group_basic_fields(data['plugin_name'],
                                    data['hadoop_version'], data)


def check_node_group_template_usage(node_group_template_id, **kwargs):
    cluster_users = []
    template_users = []

    for cluster in api.get_clusters():
        if (node_group_template_id in
            [node_group.node_group_template_id
             for node_group in cluster.node_groups]):
            cluster_users += [cluster.name]

    for cluster_template in api.get_cluster_templates():
        if (node_group_template_id in
            [node_group.node_group_template_id
             for node_group in cluster_template.node_groups]):
            template_users += [cluster_template.name]

    if cluster_users or template_users:
        raise ex.InvalidReferenceException(
            _("Node group template %(template)s is in use by "
              "cluster templates: %(users)s; and clusters: %(clusters)s") %
            {'template': node_group_template_id,
             'users': template_users and ', '.join(template_users) or 'N/A',
             'clusters': cluster_users and ', '.join(cluster_users) or 'N/A'})


def check_node_group_template_update(data, **kwargs):
    if data.get('plugin_name') and not data.get('hadoop_version'):
        raise ex.InvalidReferenceException(
            _("You must specify a hadoop_version value"
              "for your plugin_name"))
    if data.get('hadoop_version') and not data.get('plugin_name'):
        raise ex.InvalidReferenceException(
            _("You must specify a plugin_name"
              "for your hadoop_version value"))

    if data.get('plugin_name'):
        b.check_plugin_name_exists(data['plugin_name'])
        b.check_plugin_supports_version(data['plugin_name'],
                                        data['hadoop_version'])
        b.check_node_group_basic_fields(data['plugin_name'],
                                        data['hadoop_version'], data)
