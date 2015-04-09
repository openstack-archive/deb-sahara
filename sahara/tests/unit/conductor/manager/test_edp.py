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

import copy
import datetime

import testtools

from sahara import context
from sahara import exceptions as ex
import sahara.tests.unit.conductor.base as test_base
from sahara.tests.unit.conductor.manager import test_clusters
from sahara.utils import edp


SAMPLE_DATA_SOURCE = {
    "tenant_id": "test_tenant",
    "name": "ngt_test",
    "description": "test_desc",
    "type": "Cassandra",
    "url": "localhost:1080",
    "credentials": {
        "user": "test",
        "password": "123"
    }
}

SAMPLE_JOB = {
    "tenant_id": "test_tenant",
    "name": "job_test",
    "description": "test_desc",
    "type": edp.JOB_TYPE_PIG,
    "mains": []
}

SAMPLE_JOB_EXECUTION = {
    "tenant_id": "tenant_id",
    "return_code": "1",
    "job_id": "undefined",
    "input_id": "undefined",
    "output_id": "undefined",
    "start_time": datetime.datetime.now(),
    "cluster_id": None
}

SAMPLE_CONF_JOB_EXECUTION = {
    "tenant_id": "tenant_id",
    "progress": "0.1",
    "return_code": "1",
    "job_id": "undefined",
    "input_id": "undefined",
    "output_id": "undefined",
    "cluster_id": None,
    "job_configs": {
        "conf2": "value_je",
        "conf3": "value_je"
    }
}

BINARY_DATA = "vU}\x97\x1c\xdf\xa686\x08\xf2\tf\x0b\xb1}"

SAMPLE_JOB_BINARY_INTERNAL = {
    "tenant_id": "test_tenant",
    "name": "job_test",
    "data": BINARY_DATA
}


SAMPLE_JOB_BINARY = {
    "tenant_id": "test_tenant",
    "name": "job_binary_test",
    "description": "test_dec",
    "url": "internal-db://test_binary",
}


class DataSourceTest(test_base.ConductorManagerTestCase):
    def __init__(self, *args, **kwargs):
        super(DataSourceTest, self).__init__(
            checks=[
                lambda: SAMPLE_DATA_SOURCE
            ], *args, **kwargs)

    def test_crud_operation_create_list_delete(self):
        ctx = context.ctx()
        self.api.data_source_create(ctx, SAMPLE_DATA_SOURCE)

        lst = self.api.data_source_get_all(ctx)
        self.assertEqual(1, len(lst))

        ds_id = lst[0]['id']
        self.api.data_source_destroy(ctx, ds_id)

        lst = self.api.data_source_get_all(ctx)
        self.assertEqual(0, len(lst))

    def test_duplicate_data_source_create(self):
        ctx = context.ctx()
        self.api.data_source_create(ctx, SAMPLE_DATA_SOURCE)
        with testtools.ExpectedException(ex.DBDuplicateEntry):
            self.api.data_source_create(ctx, SAMPLE_DATA_SOURCE)

    def test_data_source_fields(self):
        ctx = context.ctx()
        ctx.tenant_id = SAMPLE_DATA_SOURCE['tenant_id']
        ds_db_obj_id = self.api.data_source_create(ctx,
                                                   SAMPLE_DATA_SOURCE)['id']

        ds_db_obj = self.api.data_source_get(ctx, ds_db_obj_id)
        self.assertIsInstance(ds_db_obj, dict)

        for key, val in SAMPLE_DATA_SOURCE.items():
            self.assertEqual(val, ds_db_obj.get(key),
                             "Key not found %s" % key)

    def test_data_source_delete(self):
        ctx = context.ctx()
        db_obj_ds = self.api.data_source_create(ctx, SAMPLE_DATA_SOURCE)
        _id = db_obj_ds['id']

        self.api.data_source_destroy(ctx, _id)

        with testtools.ExpectedException(ex.NotFoundException):
            self.api.data_source_destroy(ctx, _id)

    def test_data_source_search(self):
        ctx = context.ctx()
        ctx.tenant_id = SAMPLE_DATA_SOURCE['tenant_id']
        self.api.data_source_create(ctx, SAMPLE_DATA_SOURCE)

        lst = self.api.data_source_get_all(ctx)
        self.assertEqual(1, len(lst))

        kwargs = {'name': SAMPLE_DATA_SOURCE['name'],
                  'tenant_id': SAMPLE_DATA_SOURCE['tenant_id']}
        lst = self.api.data_source_get_all(ctx, **kwargs)
        self.assertEqual(1, len(lst))

        # Valid field but no matching value
        kwargs = {'name': SAMPLE_DATA_SOURCE['name']+"foo"}
        lst = self.api.data_source_get_all(ctx, **kwargs)
        self.assertEqual(0, len(lst))

        # Invalid field
        lst = self.api.data_source_get_all(ctx, **{'badfield': 'somevalue'})
        self.assertEqual(0, len(lst))

    def test_data_source_count_in(self):
        ctx = context.ctx()
        ctx.tenant_id = SAMPLE_DATA_SOURCE['tenant_id']
        src = copy.copy(SAMPLE_DATA_SOURCE)
        self.api.data_source_create(ctx, src)

        cnt = self.api.data_source_count(ctx, name='ngt_test')
        self.assertEqual(1, cnt)

        cnt = self.api.data_source_count(ctx, name=('ngt_test',
                                                    'test2', 'test3'))
        self.assertEqual(1, cnt)

        cnt = self.api.data_source_count(ctx, name=('test1',
                                                    'test2', 'test3'))
        self.assertEqual(0, cnt)

        lst = self.api.data_source_get_all(ctx, name='ngt_test')
        myid = lst[0]['id']
        cnt = self.api.data_source_count(ctx,
                                         name=('ngt_test', 'test2', 'test3'),
                                         id=myid)
        self.assertEqual(1, cnt)

        cnt = self.api.data_source_count(ctx,
                                         name=('ngt_test', 'test2', 'test3'),
                                         id=(myid, '2'))
        self.assertEqual(1, cnt)

    def test_data_source_count_like(self):
        ctx = context.ctx()
        ctx.tenant_id = SAMPLE_DATA_SOURCE['tenant_id']
        src = copy.copy(SAMPLE_DATA_SOURCE)
        self.api.data_source_create(ctx, src)

        cnt = self.api.data_source_count(ctx, name='ngt_test')
        self.assertEqual(1, cnt)

        cnt = self.api.data_source_count(ctx, name='ngt%')
        self.assertEqual(1, cnt)

        cnt = self.api.data_source_count(ctx,
                                         name=('ngt_test',),
                                         url='localhost%')
        self.assertEqual(1, cnt)

        cnt = self.api.data_source_count(ctx,
                                         name=('ngt_test',),
                                         url='localhost')
        self.assertEqual(0, cnt)


class JobExecutionTest(test_base.ConductorManagerTestCase):
    def test_crud_operation_create_list_delete_update(self):
        ctx = context.ctx()
        job = self.api.job_create(ctx, SAMPLE_JOB)
        ds_input = self.api.data_source_create(ctx, SAMPLE_DATA_SOURCE)
        SAMPLE_DATA_OUTPUT = copy.copy(SAMPLE_DATA_SOURCE)
        SAMPLE_DATA_OUTPUT['name'] = 'output'
        ds_output = self.api.data_source_create(ctx, SAMPLE_DATA_OUTPUT)

        SAMPLE_JOB_EXECUTION['job_id'] = job['id']
        SAMPLE_JOB_EXECUTION['input_id'] = ds_input['id']
        SAMPLE_JOB_EXECUTION['output_id'] = ds_output['id']

        self.api.job_execution_create(ctx, SAMPLE_JOB_EXECUTION)

        lst = self.api.job_execution_get_all(ctx)
        self.assertEqual(1, len(lst))

        count = self.api.job_execution_count(ctx)
        self.assertEqual(1, count)

        job_ex_id = lst[0]['id']

        self.assertIsNone(lst[0]['info'])
        new_info = {"status": edp.JOB_STATUS_PENDING}
        self.api.job_execution_update(ctx, job_ex_id, {'info': new_info})
        updated_job = self.api.job_execution_get(ctx, job_ex_id)
        self.assertEqual(new_info, updated_job['info'])
        self.assertEqual(SAMPLE_JOB_EXECUTION['start_time'],
                         updated_job['start_time'])

        self.api.job_execution_destroy(ctx, job_ex_id)

        with testtools.ExpectedException(ex.NotFoundException):
            self.api.job_execution_update(ctx, job_ex_id, {'info': new_info})

        with testtools.ExpectedException(ex.NotFoundException):
            self.api.job_execution_destroy(ctx, job_ex_id)

        lst = self.api.job_execution_get_all(ctx)
        self.assertEqual(0, len(lst))

    def test_crud_operation_on_configured_jobs(self):
        ctx = context.ctx()
        job = self.api.job_create(ctx, SAMPLE_JOB)
        ds_input = self.api.data_source_create(ctx, SAMPLE_DATA_SOURCE)
        SAMPLE_DATA_OUTPUT = copy.copy(SAMPLE_DATA_SOURCE)
        SAMPLE_DATA_OUTPUT['name'] = 'output'
        ds_output = self.api.data_source_create(ctx, SAMPLE_DATA_OUTPUT)

        SAMPLE_CONF_JOB_EXECUTION['job_id'] = job['id']
        SAMPLE_CONF_JOB_EXECUTION['input_id'] = ds_input['id']
        SAMPLE_CONF_JOB_EXECUTION['output_id'] = ds_output['id']

        self.api.job_execution_create(ctx, SAMPLE_CONF_JOB_EXECUTION)

        lst = self.api.job_execution_get_all(ctx)
        self.assertEqual(1, len(lst))

        job_ex = lst[0]
        configs = {
            'conf2': 'value_je',
            'conf3': 'value_je'
        }
        self.assertEqual(configs, job_ex['job_configs'])

    def test_deletion_constraints_on_data_and_jobs(self):
        ctx = context.ctx()
        job = self.api.job_create(ctx, SAMPLE_JOB)
        ds_input = self.api.data_source_create(ctx, SAMPLE_DATA_SOURCE)
        SAMPLE_DATA_OUTPUT = copy.copy(SAMPLE_DATA_SOURCE)
        SAMPLE_DATA_OUTPUT['name'] = 'output'
        ds_output = self.api.data_source_create(ctx, SAMPLE_DATA_OUTPUT)

        SAMPLE_CONF_JOB_EXECUTION['job_id'] = job['id']
        SAMPLE_CONF_JOB_EXECUTION['input_id'] = ds_input['id']
        SAMPLE_CONF_JOB_EXECUTION['output_id'] = ds_output['id']

        self.api.job_execution_create(ctx, SAMPLE_CONF_JOB_EXECUTION)

        with testtools.ExpectedException(ex.DeletionFailed):
            self.api.data_source_destroy(ctx, ds_input['id'])
        with testtools.ExpectedException(ex.DeletionFailed):
            self.api.data_source_destroy(ctx, ds_output['id'])
        with testtools.ExpectedException(ex.DeletionFailed):
            self.api.job_destroy(ctx, job['id'])

    def test_job_execution_search(self):
        ctx = context.ctx()
        job = self.api.job_create(ctx, SAMPLE_JOB)
        ds_input = self.api.data_source_create(ctx, SAMPLE_DATA_SOURCE)
        SAMPLE_DATA_OUTPUT = copy.copy(SAMPLE_DATA_SOURCE)
        SAMPLE_DATA_OUTPUT['name'] = 'output'
        ds_output = self.api.data_source_create(ctx, SAMPLE_DATA_OUTPUT)

        SAMPLE_JOB_EXECUTION['job_id'] = job['id']
        SAMPLE_JOB_EXECUTION['input_id'] = ds_input['id']
        SAMPLE_JOB_EXECUTION['output_id'] = ds_output['id']

        ctx.tenant_id = SAMPLE_JOB_EXECUTION['tenant_id']
        self.api.job_execution_create(ctx, SAMPLE_JOB_EXECUTION)

        lst = self.api.job_execution_get_all(ctx)
        self.assertEqual(1, len(lst))

        kwargs = {'tenant_id': SAMPLE_JOB_EXECUTION['tenant_id']}
        lst = self.api.job_execution_get_all(ctx, **kwargs)
        self.assertEqual(1, len(lst))

        # Valid field but no matching value
        kwargs = {'job_id': SAMPLE_JOB_EXECUTION['job_id']+"foo"}
        lst = self.api.job_execution_get_all(ctx, **kwargs)
        self.assertEqual(0, len(lst))

        # Invalid field
        lst = self.api.job_execution_get_all(ctx, **{'badfield': 'somevalue'})
        self.assertEqual(0, len(lst))

    def test_job_execution_advanced_search(self):
        ctx = context.ctx()
        job = self.api.job_create(ctx, SAMPLE_JOB)
        ds_input = self.api.data_source_create(ctx, SAMPLE_DATA_SOURCE)
        SAMPLE_DATA_OUTPUT = copy.copy(SAMPLE_DATA_SOURCE)
        SAMPLE_DATA_OUTPUT['name'] = 'output'
        ds_output = self.api.data_source_create(ctx, SAMPLE_DATA_OUTPUT)

        # Create a cluster
        cl1 = self.api.cluster_create(ctx, test_clusters.SAMPLE_CLUSTER)

        # Create a second cluster with a different name
        cl2_vals = copy.copy(test_clusters.SAMPLE_CLUSTER)
        cl2_vals['name'] = 'test_cluster2'
        cl2 = self.api.cluster_create(ctx, cl2_vals)

        my_sample_job_exec = copy.copy(SAMPLE_JOB_EXECUTION)

        my_sample_job_exec['job_id'] = job['id']
        my_sample_job_exec['input_id'] = ds_input['id']
        my_sample_job_exec['output_id'] = ds_output['id']
        my_sample_job_exec['cluster_id'] = cl1['id']

        # Run job on cluster 1
        self.api.job_execution_create(ctx, my_sample_job_exec)

        # Run the same job on cluster 2 and set status
        my_sample_job_exec['cluster_id'] = cl2['id']
        my_sample_job_exec['info'] = {'status': 'KiLLeD'}
        self.api.job_execution_create(ctx, my_sample_job_exec)

        # Search only with job exeuction fields (finds both)
        lst = self.api.job_execution_get_all(ctx, **{'return_code': 1})
        self.assertEqual(2, len(lst))

        # Search on cluster name
        kwargs = {'cluster.name': cl1['name'],
                  'return_code': 1}
        lst = self.api.job_execution_get_all(ctx, **kwargs)
        self.assertEqual(1, len(lst))

        # Search on cluster name and job name
        kwargs = {'cluster.name': cl1['name'],
                  'job.name': SAMPLE_JOB['name'],
                  'return_code': 1}
        lst = self.api.job_execution_get_all(ctx, **kwargs)
        self.assertEqual(1, len(lst))

        # Search on cluster name, job name, and status
        kwargs = {'cluster.name': cl2['name'],
                  'job.name': SAMPLE_JOB['name'],
                  'status': 'killed',
                  'return_code': 1}
        lst = self.api.job_execution_get_all(ctx, **kwargs)
        self.assertEqual(1, len(lst))

        # Search on job name (finds both)
        kwargs = {'job.name': SAMPLE_JOB['name'],
                  'return_code': 1}
        lst = self.api.job_execution_get_all(ctx, **kwargs)
        self.assertEqual(2, len(lst))

        # invalid cluster name value
        kwargs = {'cluster.name': cl1['name']+'foo',
                  'job.name': SAMPLE_JOB['name']}
        lst = self.api.job_execution_get_all(ctx, **kwargs)
        self.assertEqual(0, len(lst))

        # invalid job name value
        kwargs = {'cluster.name': cl1['name'],
                  'job.name': SAMPLE_JOB['name']+'foo'}
        lst = self.api.job_execution_get_all(ctx, **kwargs)
        self.assertEqual(0, len(lst))

        # invalid status value
        kwargs = {'cluster.name': cl1['name'],
                  'status': 'PENDING'}
        lst = self.api.job_execution_get_all(ctx, **kwargs)
        self.assertEqual(0, len(lst))


class JobTest(test_base.ConductorManagerTestCase):
    def __init__(self, *args, **kwargs):
        super(JobTest, self).__init__(
            checks=[
                lambda: SAMPLE_JOB
            ], *args, **kwargs)

    def test_crud_operation_create_list_delete_update(self):
        ctx = context.ctx()

        self.api.job_create(ctx, SAMPLE_JOB)

        lst = self.api.job_get_all(ctx)
        self.assertEqual(1, len(lst))

        jo_id = lst[0]['id']

        update_jo = self.api.job_update(ctx, jo_id,
                                        {'description': 'update'})
        self.assertEqual('update', update_jo['description'])

        self.api.job_destroy(ctx, jo_id)

        lst = self.api.job_get_all(ctx)
        self.assertEqual(0, len(lst))

        with testtools.ExpectedException(ex.NotFoundException):
            self.api.job_destroy(ctx, jo_id)

    def test_job_fields(self):
        ctx = context.ctx()
        ctx.tenant_id = SAMPLE_JOB['tenant_id']
        job_id = self.api.job_create(ctx, SAMPLE_JOB)['id']

        job = self.api.job_get(ctx, job_id)
        self.assertIsInstance(job, dict)

        for key, val in SAMPLE_JOB.items():
            self.assertEqual(val, job.get(key),
                             "Key not found %s" % key)

    def test_job_search(self):
        ctx = context.ctx()
        ctx.tenant_id = SAMPLE_JOB['tenant_id']
        self.api.job_create(ctx, SAMPLE_JOB)

        lst = self.api.job_get_all(ctx)
        self.assertEqual(1, len(lst))

        kwargs = {'name': SAMPLE_JOB['name'],
                  'tenant_id': SAMPLE_JOB['tenant_id']}
        lst = self.api.job_get_all(ctx, **kwargs)
        self.assertEqual(1, len(lst))

        # Valid field but no matching value
        lst = self.api.job_get_all(ctx, **{'name': SAMPLE_JOB['name']+"foo"})
        self.assertEqual(0, len(lst))

        # Invalid field
        lst = self.api.job_get_all(ctx, **{'badfield': 'somevalue'})
        self.assertEqual(0, len(lst))


class JobBinaryInternalTest(test_base.ConductorManagerTestCase):
    def __init__(self, *args, **kwargs):
        super(JobBinaryInternalTest, self).__init__(
            checks=[
                lambda: SAMPLE_JOB_BINARY_INTERNAL
            ], *args, **kwargs)

    def test_crud_operation_create_list_delete(self):
        ctx = context.ctx()

        self.api.job_binary_internal_create(ctx, SAMPLE_JOB_BINARY_INTERNAL)

        lst = self.api.job_binary_internal_get_all(ctx)
        self.assertEqual(1, len(lst))

        job_bin_int_id = lst[0]['id']
        self.api.job_binary_internal_destroy(ctx, job_bin_int_id)

        lst = self.api.job_binary_internal_get_all(ctx)
        self.assertEqual(0, len(lst))

        with testtools.ExpectedException(ex.NotFoundException):
            self.api.job_binary_internal_destroy(ctx, job_bin_int_id)

    def test_duplicate_job_binary_internal_create(self):
        ctx = context.ctx()
        self.api.job_binary_internal_create(ctx, SAMPLE_JOB_BINARY_INTERNAL)
        with testtools.ExpectedException(ex.DBDuplicateEntry):
            self.api.job_binary_internal_create(ctx,
                                                SAMPLE_JOB_BINARY_INTERNAL)

    def test_job_binary_internal_get_raw(self):
        ctx = context.ctx()

        id = self.api.job_binary_internal_create(ctx,
                                                 SAMPLE_JOB_BINARY_INTERNAL
                                                 )['id']
        data = self.api.job_binary_internal_get_raw_data(ctx, id)
        self.assertEqual(SAMPLE_JOB_BINARY_INTERNAL["data"], data)

        self.api.job_binary_internal_destroy(ctx, id)

        data = self.api.job_binary_internal_get_raw_data(ctx, id)
        self.assertIsNone(data)

    def test_job_binary_internal_fields(self):
        ctx = context.ctx()
        ctx.tenant_id = SAMPLE_JOB_BINARY_INTERNAL['tenant_id']
        id = self.api.job_binary_internal_create(
            ctx, SAMPLE_JOB_BINARY_INTERNAL)['id']

        internal = self.api.job_binary_internal_get(ctx, id)
        self.assertIsInstance(internal, dict)
        with testtools.ExpectedException(KeyError):
            internal["data"]

        internal["data"] = self.api.job_binary_internal_get_raw_data(ctx, id)
        for key, val in SAMPLE_JOB_BINARY_INTERNAL.items():
            if key == "datasize":
                self.assertEqual(len(BINARY_DATA), internal["datasize"])
            else:
                self.assertEqual(val, internal.get(key),
                                 "Key not found %s" % key)

    def test_job_binary_internal_search(self):
        ctx = context.ctx()
        ctx.tenant_id = SAMPLE_JOB_BINARY_INTERNAL['tenant_id']
        self.api.job_binary_internal_create(ctx, SAMPLE_JOB_BINARY_INTERNAL)

        lst = self.api.job_binary_internal_get_all(ctx)
        self.assertEqual(1, len(lst))

        kwargs = {'name': SAMPLE_JOB_BINARY_INTERNAL['name'],
                  'tenant_id': SAMPLE_JOB_BINARY_INTERNAL['tenant_id']}
        lst = self.api.job_binary_internal_get_all(ctx, **kwargs)
        self.assertEqual(1, len(lst))

        # Valid field but no matching value
        kwargs = {'name': SAMPLE_JOB_BINARY_INTERNAL['name']+"foo"}
        lst = self.api.job_binary_internal_get_all(ctx, **kwargs)
        self.assertEqual(0, len(lst))

        # Invalid field
        lst = self.api.job_binary_internal_get_all(ctx, **{'badfield': 'junk'})
        self.assertEqual(0, len(lst))


class JobBinaryTest(test_base.ConductorManagerTestCase):
    def __init__(self, *args, **kwargs):
        super(JobBinaryTest, self).__init__(
            checks=[
                lambda: SAMPLE_JOB_BINARY
            ], *args, **kwargs)

    def test_crud_operation_create_list_delete(self):
        ctx = context.ctx()

        self.api.job_binary_create(ctx, SAMPLE_JOB_BINARY)

        lst = self.api.job_binary_get_all(ctx)
        self.assertEqual(1, len(lst))

        job_binary_id = lst[0]['id']
        self.api.job_binary_destroy(ctx, job_binary_id)

        lst = self.api.job_binary_get_all(ctx)
        self.assertEqual(0, len(lst))

        with testtools.ExpectedException(ex.NotFoundException):
            self.api.job_binary_destroy(ctx, job_binary_id)

    def test_job_binary_fields(self):
        ctx = context.ctx()
        ctx.tenant_id = SAMPLE_JOB_BINARY['tenant_id']
        job_binary_id = self.api.job_binary_create(ctx,
                                                   SAMPLE_JOB_BINARY)['id']

        job_binary = self.api.job_binary_get(ctx, job_binary_id)
        self.assertIsInstance(job_binary, dict)

        for key, val in SAMPLE_JOB_BINARY.items():
            self.assertEqual(val, job_binary.get(key),
                             "Key not found %s" % key)

    def _test_job_binary_referenced(self, reference):
        ctx = context.ctx()
        job_binary_id = self.api.job_binary_create(ctx,
                                                   SAMPLE_JOB_BINARY)['id']

        job_values = copy.copy(SAMPLE_JOB)
        job_values[reference] = [job_binary_id]
        job_id = self.api.job_create(ctx, job_values)['id']

        # Delete while referenced, fails
        with testtools.ExpectedException(ex.DeletionFailed):
            self.api.job_binary_destroy(ctx, job_binary_id)

        # Delete while not referenced
        self.api.job_destroy(ctx, job_id)
        self.api.job_binary_destroy(ctx, job_binary_id)
        lst = self.api.job_binary_get_all(ctx)
        self.assertEqual(0, len(lst))

    def test_job_binary_referenced_mains(self):
        self._test_job_binary_referenced("mains")

    def test_job_binary_referenced_libs(self):
        self._test_job_binary_referenced("libs")

    def test_duplicate_job_binary_create(self):
        ctx = context.ctx()
        self.api.job_binary_create(ctx, SAMPLE_JOB_BINARY)
        with testtools.ExpectedException(ex.DBDuplicateEntry):
            self.api.job_binary_create(ctx,
                                       SAMPLE_JOB_BINARY)

    def test_job_binary_search(self):
        ctx = context.ctx()
        ctx.tenant_id = SAMPLE_JOB_BINARY['tenant_id']
        self.api.job_binary_create(ctx, SAMPLE_JOB_BINARY)

        lst = self.api.job_binary_get_all(ctx)
        self.assertEqual(1, len(lst))

        kwargs = {'name': SAMPLE_JOB_BINARY['name'],
                  'tenant_id': SAMPLE_JOB_BINARY['tenant_id']}
        lst = self.api.job_binary_get_all(ctx, **kwargs)
        self.assertEqual(1, len(lst))

        # Valid field but no matching value
        kwargs = {'name': SAMPLE_JOB_BINARY['name']+"foo"}
        lst = self.api.job_binary_get_all(ctx, **kwargs)
        self.assertEqual(0, len(lst))

        # Invalid field
        lst = self.api.job_binary_get_all(ctx, **{'badfield': 'somevalue'})
        self.assertEqual(0, len(lst))
