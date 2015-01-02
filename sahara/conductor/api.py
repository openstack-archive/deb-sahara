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

"""Handles all requests to the conductor service."""

from oslo.config import cfg

from sahara.conductor import manager
from sahara.conductor import resource as r
from sahara.openstack.common import log as logging


conductor_opts = [
    cfg.BoolOpt('use_local',
                default=True,
                help='Perform sahara-conductor operations locally.'),
]

conductor_group = cfg.OptGroup(name='conductor',
                               title='Conductor Options')

CONF = cfg.CONF
CONF.register_group(conductor_group)
CONF.register_opts(conductor_opts, conductor_group)

LOG = logging.getLogger(__name__)


def _get_id(obj):
    """Return object id.

    Allows usage of both an object or an object's ID as a parameter when
    dealing with relationships.
    """
    try:
        return obj.id
    except AttributeError:
        return obj


class LocalApi(object):
    """A local version of the conductor API.

    It does database updates locally instead of via RPC.
    """

    def __init__(self):
        self._manager = manager.ConductorManager()

    # Cluster ops

    @r.wrap(r.ClusterResource)
    def cluster_get(self, context, cluster):
        """Return the cluster or None if it does not exist."""
        return self._manager.cluster_get(context, _get_id(cluster))

    @r.wrap(r.ClusterResource)
    def cluster_get_all(self, context, **kwargs):
        """Get all clusters filtered by **kwargs.

        e.g.  cluster_get_all(plugin_name='vanilla', hadoop_version='1.1')
        """
        return self._manager.cluster_get_all(context, **kwargs)

    @r.wrap(r.ClusterResource)
    def cluster_create(self, context, values):
        """Create a cluster from the values dictionary.

        :returns: the created cluster.
        """
        return self._manager.cluster_create(context, values)

    @r.wrap(r.ClusterResource)
    def cluster_update(self, context, cluster, values):
        """Update the cluster with the given values dictionary.

        :returns: the updated cluster.
        """
        return self._manager.cluster_update(context, _get_id(cluster),
                                            values)

    def cluster_destroy(self, context, cluster):
        """Destroy the cluster or raise if it does not exist.

        :returns: None.
        """
        self._manager.cluster_destroy(context, _get_id(cluster))

    # Node Group ops

    def node_group_add(self, context, cluster, values):
        """Create a node group from the values dictionary.

        :returns: ID of the created node group.
        """
        return self._manager.node_group_add(context, _get_id(cluster), values)

    def node_group_update(self, context, node_group, values):
        """Update the node group with the given values dictionary.

        :returns: None.
        """
        self._manager.node_group_update(context, _get_id(node_group), values)

    def node_group_remove(self, context, node_group):
        """Destroy the node group or raise if it does not exist.

        :returns: None.
        """
        self._manager.node_group_remove(context, _get_id(node_group))

    # Instance ops

    def instance_add(self, context, node_group, values):
        """Create an instance from the values dictionary.

        :returns: ID of the created instance.
        """
        return self._manager.instance_add(context, _get_id(node_group), values)

    def instance_update(self, context, instance, values):
        """Update the instance with the given values dictionary.

        :returns: None.
        """
        self._manager.instance_update(context, _get_id(instance), values)

    def instance_remove(self, context, instance):
        """Destroy the instance or raise if it does not exist.

        :returns: None.
        """
        self._manager.instance_remove(context, _get_id(instance))

    # Volumes ops

    def append_volume(self, context, instance, volume_id):
        """Append volume_id to instance."""
        self._manager.append_volume(context, _get_id(instance), volume_id)

    def remove_volume(self, context, instance, volume_id):
        """Remove volume_id in instance."""
        self._manager.remove_volume(context, _get_id(instance), volume_id)

    # Cluster Template ops

    @r.wrap(r.ClusterTemplateResource)
    def cluster_template_get(self, context, cluster_template):
        """Return the cluster template or None if it does not exist."""
        return self._manager.cluster_template_get(context,
                                                  _get_id(cluster_template))

    @r.wrap(r.ClusterTemplateResource)
    def cluster_template_get_all(self, context, **kwargs):
        """Get all cluster templates filtered by **kwargs.

        e.g.  cluster_template_get_all(plugin_name='vanilla',
                                       hadoop_version='1.1')
        """
        return self._manager.cluster_template_get_all(context, **kwargs)

    @r.wrap(r.ClusterTemplateResource)
    def cluster_template_create(self, context, values):
        """Create a cluster template from the values dictionary.

        :returns: the created cluster template
        """
        return self._manager.cluster_template_create(context, values)

    def cluster_template_destroy(self, context, cluster_template):
        """Destroy the cluster template or raise if it does not exist.

        :returns: None
        """
        self._manager.cluster_template_destroy(context,
                                               _get_id(cluster_template))

    # Node Group Template ops

    @r.wrap(r.NodeGroupTemplateResource)
    def node_group_template_get(self, context, node_group_template):
        """Return the node group template or None if it does not exist."""
        return self._manager.node_group_template_get(
            context, _get_id(node_group_template))

    @r.wrap(r.NodeGroupTemplateResource)
    def node_group_template_get_all(self, context, **kwargs):
        """Get all node group templates filtered by **kwargs.

        e.g.  node_group_template_get_all(plugin_name='vanilla',
                                          hadoop_version='1.1')
        """
        return self._manager.node_group_template_get_all(context, **kwargs)

    @r.wrap(r.NodeGroupTemplateResource)
    def node_group_template_create(self, context, values):
        """Create a node group template from the values dictionary.

        :returns: the created node group template
        """
        return self._manager.node_group_template_create(context, values)

    def node_group_template_destroy(self, context, node_group_template):
        """Destroy the node group template or raise if it does not exist.

        :returns: None
        """
        self._manager.node_group_template_destroy(context,
                                                  _get_id(node_group_template))

    # Data Source ops

    @r.wrap(r.DataSource)
    def data_source_get(self, context, data_source):
        """Return the Data Source or None if it does not exist."""
        return self._manager.data_source_get(context, _get_id(data_source))

    @r.wrap(r.DataSource)
    def data_source_get_all(self, context, **kwargs):
        """Get all Data Sources filtered by **kwargs.

        e.g.  data_source_get_all(name='myfile', type='swift')
        """
        return self._manager.data_source_get_all(context, **kwargs)

    @r.wrap(r.DataSource)
    def data_source_create(self, context, values):
        """Create a Data Source from the values dictionary."""
        return self._manager.data_source_create(context, values)

    def data_source_destroy(self, context, data_source):
        """Destroy the Data Source or raise if it does not exist."""
        self._manager.data_source_destroy(context, _get_id(data_source))

    # JobExecution ops

    @r.wrap(r.JobExecution)
    def job_execution_get(self, context, job_execution):
        """Return the JobExecution or None if it does not exist."""
        return self._manager.job_execution_get(context,
                                               _get_id(job_execution))

    @r.wrap(r.JobExecution)
    def job_execution_get_all(self, context, **kwargs):
        """Get all JobExecutions filtered by **kwargs.

        kwargs key values may be the names of fields in a JobExecution
        plus the following special values with the indicated meaning:

        'cluster.name' -- name of the Cluster referenced by the JobExecution
        'job.name' -- name of the Job referenced by the JobExecution
        'status' -- JobExecution['info']['status']

        e.g. job_execution_get_all(cluster_id=12, input_id=123)
             job_execution_get_all(**{'cluster.name': 'test',
                                      'job.name': 'wordcount'})
        """
        return self._manager.job_execution_get_all(context, **kwargs)

    def job_execution_count(self, context, **kwargs):
        """Count number of JobExecutions filtered by **kwargs.

        e.g. job_execution_count(cluster_id=12, input_id=123)
        """
        return self._manager.job_execution_count(context, **kwargs)

    @r.wrap(r.JobExecution)
    def job_execution_create(self, context, values):
        """Create a JobExecution from the values dictionary."""
        return self._manager.job_execution_create(context, values)

    @r.wrap(r.JobExecution)
    def job_execution_update(self, context, job_execution, values):
        """Update the JobExecution or raise if it does not exist."""
        return self._manager.job_execution_update(context,
                                                  _get_id(job_execution),
                                                  values)

    def job_execution_destroy(self, context, job_execution):
        """Destroy the JobExecution or raise if it does not exist."""
        self._manager.job_execution_destroy(context, _get_id(job_execution))

    # Job ops

    @r.wrap(r.Job)
    def job_get(self, context, job):
        """Return the Job or None if it does not exist."""
        return self._manager.job_get(context, _get_id(job))

    @r.wrap(r.Job)
    def job_get_all(self, context, **kwargs):
        """Get all Jobs filtered by **kwargs.

        e.g.  job_get_all(name='myjob', type='MapReduce')
        """
        return self._manager.job_get_all(context, **kwargs)

    @r.wrap(r.Job)
    def job_create(self, context, values):
        """Create a Job from the values dictionary."""
        return self._manager.job_create(context, values)

    def job_update(self, context, job, values):
        """Update the Job or raise if it does not exist."""
        return self._manager.job_update(context, _get_id(job),
                                        values)

    def job_destroy(self, context, job):
        """Destroy the Job or raise if it does not exist."""
        self._manager.job_destroy(context, _get_id(job))

    def job_main_name(self, context, job):
        """Return the name of the first main JobBinary or None.

        At present the 'mains' element is expected to contain a single element.
        In the future if 'mains' contains more than one element we will need
        a scheme or convention for retrieving a name from the list of binaries.

        :param job: This is expected to be a Job object
        """
        if job.mains:
            binary = self.job_binary_get(context, job.mains[0])
            if binary is not None:
                return binary["name"]
        return None

    # JobBinary ops

    @r.wrap(r.JobBinary)
    def job_binary_get_all(self, context, **kwargs):
        """Get all JobBinarys filtered by **kwargs.

        e.g.  job_binary_get_all(name='wordcount.jar')
        """
        return self._manager.job_binary_get_all(context, **kwargs)

    @r.wrap(r.JobBinary)
    def job_binary_get(self, context, job_binary):
        """Return the JobBinary or None if it does not exist."""
        return self._manager.job_binary_get(context, _get_id(job_binary))

    @r.wrap(r.JobBinary)
    def job_binary_create(self, context, values):
        """Create a JobBinary from the values dictionary."""
        return self._manager.job_binary_create(context, values)

    def job_binary_destroy(self, context, job_binary):
        """Destroy the JobBinary or raise if it does not exist."""
        self._manager.job_binary_destroy(context, _get_id(job_binary))

    # JobBinaryInternal ops

    @r.wrap(r.JobBinaryInternal)
    def job_binary_internal_get_all(self, context, **kwargs):
        """Get all JobBinaryInternals filtered by **kwargs.

        e.g.  cluster_get_all(name='wordcount.jar')
        """
        return self._manager.job_binary_internal_get_all(context, **kwargs)

    @r.wrap(r.JobBinaryInternal)
    def job_binary_internal_get(self, context, job_binary_internal):
        """Return the JobBinaryInternal or None if it does not exist."""
        return self._manager.job_binary_internal_get(
            context,
            _get_id(job_binary_internal))

    @r.wrap(r.JobBinaryInternal)
    def job_binary_internal_create(self, context, values):
        """Create a JobBinaryInternal from the values dictionary."""
        return self._manager.job_binary_internal_create(context, values)

    def job_binary_internal_destroy(self, context, job_binary_internal_id):
        """Destroy the JobBinaryInternal or raise if it does not exist."""
        self._manager.job_binary_internal_destroy(
            context,
            _get_id(job_binary_internal_id))

    def job_binary_internal_get_raw_data(self, context,
                                         job_binary_internal_id):
        """Return the binary data field from a JobBinaryInternal."""
        return self._manager.job_binary_internal_get_raw_data(
            context,
            job_binary_internal_id)

    # Events ops

    def cluster_provision_step_add(self, context, cluster_id, values):
        """Create a cluster assigned ProvisionStep

        from the values dictionary
        """
        return self._manager.cluster_provision_step_add(
            context, cluster_id, values)

    def cluster_provision_step_update(self, context, provision_step, values):
        """Update the ProvisionStep from the values dictionary."""
        self._manager.cluster_provision_step_update(
            context, provision_step, values)

    def cluster_provision_step_get_events(self, context, provision_step):
        """Return all events from the specified ProvisionStep."""
        return self._manager.cluster_provision_step_get_events(
            context, provision_step)

    def cluster_provision_step_remove_events(self, context, provision_step):
        """Delete all event from the specified ProvisionStep."""
        self._manager.cluster_provision_step_remove_events(
            context, provision_step)

    def cluster_event_add(self, context, provision_step, values):
        """Assign new event to the specified ProvisionStep."""
        self._manager.cluster_event_add(context, provision_step, values)


class RemoteApi(LocalApi):
    """Conductor API that does updates via RPC to the ConductorManager."""

    # TODO(slukjanov): it should override _manager and only necessary functions
