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

from sahara import conductor as c
from sahara import context
from sahara import exceptions as ex
from sahara.i18n import _
from sahara.plugins import base as plugin_base
import sahara.service.validations.edp.base as b

JOB_EXEC_SCHEMA = {
    "type": "object",
    "properties": {
        "input_id": {
            "type": "string",
            "format": "uuid",
        },
        "output_id": {
            "type": "string",
            "format": "uuid",
        },
        "cluster_id": {
            "type": "string",
            "format": "uuid",
        },
        "job_configs": b.job_configs,
    },
    "additionalProperties": False,
    "required": [
        "cluster_id"
    ]
}


conductor = c.API


def _is_main_class_present(data):
    return data and 'edp.java.main_class' in data.get('job_configs',
                                                      {}).get('configs', {})


def check_main_class_present(data, job):
    if not _is_main_class_present(data):
        raise ex.InvalidDataException(
            _('%s job must specify edp.java.main_class') % job.type)


def _streaming_present(data):
    try:
        streaming = set(('edp.streaming.mapper',
                         'edp.streaming.reducer'))
        configs = set(data['job_configs']['configs'])
        return streaming.intersection(configs) == streaming
    except Exception:
        return False


def check_streaming_present(data, job):
    if not _streaming_present(data):
        raise ex.InvalidDataException(
            _("%s job must specify streaming mapper and reducer") % job.type)


def check_job_execution(data, job_id):
    ctx = context.ctx()

    cluster = conductor.cluster_get(ctx, data['cluster_id'])
    if not cluster:
        raise ex.InvalidReferenceException(
            _("Cluster with id '%s' doesn't exist") % data['cluster_id'])

    job = conductor.job_get(ctx, job_id)

    plugin = plugin_base.PLUGINS.get_plugin(cluster.plugin_name)
    edp_engine = plugin.get_edp_engine(cluster, job.type)
    if not edp_engine:
        raise ex.InvalidReferenceException(
            _("Cluster with id '%(cluster_id)s' doesn't support job type "
              "'%(job_type)s'") % {"cluster_id": cluster.id,
                                   "job_type": job.type})

    edp_engine.validate_job_execution(cluster, job, data)


def check_data_sources(data, job):
    if not ('input_id' in data and 'output_id' in data):
        raise ex.InvalidDataException(_("%s job requires 'input_id' "
                                        "and 'output_id'") % job.type)

    b.check_data_source_exists(data['input_id'])
    b.check_data_source_exists(data['output_id'])

    b.check_data_sources_are_different(data['input_id'], data['output_id'])
