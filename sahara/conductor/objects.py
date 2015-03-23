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

"""This module contains description of objects returned by the
conductor.

The actual objects returned are located in resource.py, which aim
is to hide some necessary magic. Current module describes objects
fields via docstrings and contains implementation of helper methods.
"""

import random

from oslo_config import cfg

from sahara.utils import configs
from sahara.utils import remote


CONF = cfg.CONF
CONF.import_opt('node_domain', 'sahara.config')


class Cluster(object):
    """An object representing Cluster.

    id
    name
    description
    tenant_id
    trust_id
    is_transient
    plugin_name
    hadoop_version
    cluster_configs - configs dict converted to object,
                      see the docs for details
    default_image_id
    anti_affinity
    management_private_key
    management_public_key
    user_keypair_id
    status
    status_description
    info
    extra
    rollback_info - internal information required for rollback
    sahara_info - internal information about sahara settings
    provision_progress - list of ProvisionStep objects
    node_groups - list of NodeGroup objects
    cluster_template_id
    cluster_template - ClusterTemplate object
    """

    def has_proxy_gateway(self):
        for ng in self.node_groups:
            if ng.is_proxy_gateway:
                return True

    def get_proxy_gateway_node(self):
        proxies = []
        for ng in self.node_groups:
            if ng.is_proxy_gateway and ng.instances:
                proxies += ng.instances

        if proxies:
            return random.choice(proxies)

        return None


class NodeGroup(object):
    """An object representing Node Group.

    id
    name
    flavor_id
    image_id
    image_username
    node_processes - list of node processes
    node_configs - configs dict converted to object,
                   see the docs for details
    volumes_per_node
    volumes_size
    volumes_availability_zone - name of Cinder availability zone
                                where to spawn volumes
    volume_mount_prefix
    volume_type
    floating_ip_pool - Floating IP Pool name used to assign Floating IPs to
                       instances in this Node Group
    security_groups - List of security groups for instances in this Node Group
    auto_security_group - indicates if Sahara should create additional
                          security group for the Node Group
    availability_zone - name of Nova availability zone where to spawn instances
    open_ports - List of ports that will be opened if auto_security_group is
                 True
    is_proxy_gateway - indicates if nodes from this node group should be used
                       as proxy to access other cluster nodes
    volume_local_to_instance - indicates if volumes and instances should be
                               created on the same physical host

    count
    instances - list of Instance objects
    node_group_template_id
    node_group_template - NodeGroupTemplate object

    If node group belongs to cluster:
    cluster_id - parent Cluster ID
    cluster - parent Cluster object

    If node group belongs to cluster template:
    cluster_template_id - parent ClusterTemplate ID
    cluster_template - parent ClusterTemplate object
    """

    def configuration(self):
        return configs.merge_configs(self.cluster.cluster_configs,
                                     self.node_configs)

    def storage_paths(self):
        mp = []
        for idx in range(1, self.volumes_per_node + 1):
            mp.append(self.volume_mount_prefix + str(idx))

        # Here we assume that NG's instances use ephemeral
        # drives for storage if volumes_per_node == 0
        if not mp:
            mp = ['/mnt']

        return mp

    def get_image_id(self):
        return self.image_id or self.cluster.default_image_id


class Instance(object):
    """An object representing Instance.

    id
    node_group_id - parent NodeGroup ID
    node_group - parent NodeGroup object
    instance_id - Nova instance ID
    instance_name
    internal_ip
    management_ip
    volumes
    """

    def hostname(self):
        return self.instance_name

    def fqdn(self):
        return self.instance_name + '.' + CONF.node_domain

    def remote(self):
        return remote.get_remote(self)


class ClusterTemplate(object):
    """An object representing Cluster Template.

    id
    name
    description
    cluster_configs - configs dict converted to object,
                      see the docs for details
    default_image_id
    anti_affinity
    tenant_id
    plugin_name
    hadoop_version
    node_groups - list of NodeGroup objects
    """


class NodeGroupTemplate(object):
    """An object representing Node Group Template.

    id
    name
    description
    tenant_id
    flavor_id
    image_id
    plugin_name
    hadoop_version
    node_processes - list of node processes
    node_configs - configs dict converted to object,
                   see the docs for details
    volumes_per_node
    volumes_size
    volumes_availability_zone
    volume_mount_prefix
    volume_type
    floating_ip_pool
    security_groups
    auto_security_group
    availability_zone
    is_proxy_gateway
    volume_local_to_instance
    """


# EDP Objects

class DataSource(object):
    """An object representing Data Source.

    id
    tenant_id
    name
    description
    type
    url
    credentials
    """


class JobExecution(object):
    """An object representing JobExecution

    id
    tenant_id
    job_id
    input_id
    output_id
    start_time
    end_time
    cluster_id
    info
    oozie_job_id
    return_code
    """


class Job(object):
    """An object representing Job

    id
    tenant_id
    name
    description
    type
    mains
    libs
    """


class JobBinary(object):
    """An object representing JobBinary

    id
    tenant_id
    name
    description
    url -  URLs may be the following: internal-db://URL, swift://
    extra - extra may contain not only user-password but e.g. auth-token
    """


class JobBinaryInternal(object):
    """An object representing JobBinaryInternal

    Note that the 'data' field is not returned. It uses deferred
    loading and must be requested explicitly with the
    job_binary_get_raw_data() conductor method.

    id
    tenant_id
    name
    datasize
    """

# Events ops


class ClusterProvisionStep(object):
    """An object representing cluster ProvisionStep

    id
    cluster_id
    tenant_id
    step_name
    step_type
    total
    successful
    events - list of Events objects assigned to the cluster
    """


class ClusterEvent(object):
    """An object representing events about cluster provision

    id
    node_group_id
    instance_id
    instance_name
    event_info
    successful
    step_id
    """
