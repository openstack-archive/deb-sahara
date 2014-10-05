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

from sahara.openstack.common import log as logging
from sahara.service.edp import api
from sahara.service import validation as v
from sahara.service.validations.edp import data_source as v_d_s
from sahara.service.validations.edp import job as v_j
from sahara.service.validations.edp import job_binary as v_j_b
from sahara.service.validations.edp import job_binary_internal as v_j_b_i
from sahara.service.validations.edp import job_execution as v_j_e
import sahara.utils.api as u


LOG = logging.getLogger(__name__)

rest = u.Rest('v11', __name__)


# EDP ops

@rest.post('/jobs/<job_id>/execute')
@v.check_exists(api.get_job, id='job_id')
@v.validate(v_j_e.JOB_EXEC_SCHEMA, v_j_e.check_job_execution)
def job_execute(job_id, data):
    return u.render(job_execution=api.execute_job(job_id, data).to_dict())


@rest.get('/jobs/config-hints/<job_type>')
@v.check_exists(api.get_job_config_hints, job_type='job_type')
def job_config_hints_get(job_type):
    return u.render(api.get_job_config_hints(job_type))


@rest.get('/job-executions')
def job_executions_list():
    job_executions = [je.to_dict() for je in api.job_execution_list()]
    return u.render(job_executions=job_executions)


@rest.get('/job-executions/<job_execution_id>')
@v.check_exists(api.get_job_execution, id='job_execution_id')
def job_executions(job_execution_id):
    job_execution = api.get_job_execution(job_execution_id)
    return u.render(job_execution.to_wrapped_dict())


@rest.get('/job-executions/<job_execution_id>/refresh-status')
@v.check_exists(api.get_job_execution, id='job_execution_id')
def job_executions_status(job_execution_id):
    job_execution = api.get_job_execution_status(job_execution_id)
    return u.render(job_execution.to_wrapped_dict())


@rest.get('/job-executions/<job_execution_id>/cancel')
@v.check_exists(api.get_job_execution, id='job_execution_id')
def job_executions_cancel(job_execution_id):
    job_execution = api.cancel_job_execution(job_execution_id)
    return u.render(job_execution.to_wrapped_dict())


@rest.delete('/job-executions/<job_execution_id>')
@v.check_exists(api.get_job_execution, id='job_execution_id')
def job_executions_delete(job_execution_id):
    api.delete_job_execution(job_execution_id)
    return u.render()


@rest.get('/data-sources')
def data_sources_list():
    return u.render(
        data_sources=[ds.to_dict() for ds in api.get_data_sources()])


@rest.post('/data-sources')
@v.validate(v_d_s.DATA_SOURCE_SCHEMA, v_d_s.check_data_source_create)
def data_source_register(data):
    return u.render(api.register_data_source(data).to_wrapped_dict())


@rest.get('/data-sources/<data_source_id>')
@v.check_exists(api.get_data_source, 'data_source_id')
def data_source_get(data_source_id):
    return u.render(api.get_data_source(data_source_id).to_wrapped_dict())


@rest.delete('/data-sources/<data_source_id>')
@v.check_exists(api.get_data_source, 'data_source_id')
def data_source_delete(data_source_id):
    api.delete_data_source(data_source_id)
    return u.render()


@rest.get('/jobs')
def job_list():
    return u.render(jobs=[j.to_dict() for j in api.get_jobs()])


@rest.post('/jobs')
@v.validate(v_j.JOB_SCHEMA, v_j.check_mains_libs)
def job_create(data):
    return u.render(api.create_job(data).to_wrapped_dict())


@rest.get('/jobs/<job_id>')
@v.check_exists(api.get_job, id='job_id')
def job_get(job_id):
    return u.render(api.get_job(job_id).to_wrapped_dict())


@rest.delete('/jobs/<job_id>')
@v.check_exists(api.get_job, id='job_id')
def job_delete(job_id):
    api.delete_job(job_id)
    return u.render()


@rest.post('/job-binaries')
@v.validate(v_j_b.JOB_BINARY_SCHEMA, v_j_b.check_job_binary)
def job_binary_create(data):
    return u.render(api.create_job_binary(data).to_wrapped_dict())


@rest.get('/job-binaries')
def job_binary_list():
    return u.render(binaries=[j.to_dict() for j in api.get_job_binaries()])


@rest.get('/job-binaries/<job_binary_id>')
@v.check_exists(api.get_job_binary, 'job_binary_id')
def job_binary_get(job_binary_id):
    return u.render(api.get_job_binary(job_binary_id).to_wrapped_dict())


@rest.delete('/job-binaries/<job_binary_id>')
@v.check_exists(api.get_job_binary, id='job_binary_id')
def job_binary_delete(job_binary_id):
    api.delete_job_binary(job_binary_id)
    return u.render()


@rest.put_file('/job-binary-internals/<name>')
@v.validate(None, v_j_b_i.check_job_binary_internal)
def job_binary_internal_create(**values):
    return u.render(api.create_job_binary_internal(values).to_wrapped_dict())


@rest.get('/job-binary-internals')
def job_binary_internal_list():
    return u.render(binaries=[j.to_dict() for j in
                              api.get_job_binary_internals()])


@rest.get('/job-binary-internals/<job_binary_internal_id>')
@v.check_exists(api.get_job_binary_internal, 'job_binary_internal_id')
def job_binary_internal_get(job_binary_internal_id):
    return u.render(api.get_job_binary_internal(job_binary_internal_id
                                                ).to_wrapped_dict())


@rest.delete('/job-binary-internals/<job_binary_internal_id>')
@v.check_exists(api.get_job_binary_internal, 'job_binary_internal_id')
def job_binary_internal_delete(job_binary_internal_id):
    api.delete_job_binary_internal(job_binary_internal_id)
    return u.render()


@rest.get('/job-binary-internals/<job_binary_internal_id>/data')
@v.check_exists(api.get_job_binary_internal, 'job_binary_internal_id')
def job_binary_internal_data(job_binary_internal_id):
    return api.get_job_binary_internal_data(job_binary_internal_id)


@rest.get('/job-binaries/<job_binary_id>/data')
@v.check_exists(api.get_job_binary, 'job_binary_id')
def job_binary_data(job_binary_id):
    data = api.get_job_binary_data(job_binary_id)
    if type(data) == dict:
        data = u.render(data)
    return data
