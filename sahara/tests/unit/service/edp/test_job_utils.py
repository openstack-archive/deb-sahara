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

import uuid

import mock
import six
import testtools

from sahara import conductor as cond
from sahara.service.edp import job_utils
from sahara.tests.unit.service.edp import edp_test_utils as u

conductor = cond.API


class JobUtilsTestCase(testtools.TestCase):

    def setUp(self):
        super(JobUtilsTestCase, self).setUp()

    def test_args_may_contain_data_sources(self):
        job_configs = None

        # No configs, default false
        by_name, by_uuid = job_utils.may_contain_data_source_refs(job_configs)
        self.assertFalse(by_name | by_uuid)

        # Empty configs, default false
        job_configs = {'configs': {}}
        by_name, by_uuid = job_utils.may_contain_data_source_refs(job_configs)
        self.assertFalse(by_name | by_uuid)

        job_configs['configs'] = {job_utils.DATA_SOURCE_SUBST_NAME: True,
                                  job_utils.DATA_SOURCE_SUBST_UUID: True}
        by_name, by_uuid = job_utils.may_contain_data_source_refs(job_configs)
        self.assertTrue(by_name & by_uuid)

        job_configs['configs'][job_utils.DATA_SOURCE_SUBST_NAME] = False
        by_name, by_uuid = job_utils.may_contain_data_source_refs(job_configs)
        self.assertFalse(by_name)
        self.assertTrue(by_uuid)

        job_configs['configs'][job_utils.DATA_SOURCE_SUBST_UUID] = False
        by_name, by_uuid = job_utils.may_contain_data_source_refs(job_configs)
        self.assertFalse(by_name | by_uuid)

        job_configs['configs'] = {job_utils.DATA_SOURCE_SUBST_NAME: 'True',
                                  job_utils.DATA_SOURCE_SUBST_UUID: 'Fish'}
        by_name, by_uuid = job_utils.may_contain_data_source_refs(job_configs)
        self.assertTrue(by_name)
        self.assertFalse(by_uuid)

    def test_find_possible_data_source_refs_by_name(self):
        id = six.text_type(uuid.uuid4())
        job_configs = {}
        self.assertEqual([],
                         job_utils.find_possible_data_source_refs_by_name(
                             job_configs))

        name_ref = job_utils.DATA_SOURCE_PREFIX+'name'
        name_ref2 = name_ref+'2'

        job_configs = {'args': ['first', id],
                       'configs': {'config': 'value'},
                       'params': {'param': 'value'}}
        self.assertEqual([],
                         job_utils.find_possible_data_source_refs_by_name(
                             job_configs))

        job_configs = {'args': [name_ref, id],
                       'configs': {'config': 'value'},
                       'params': {'param': 'value'}}
        self.assertEqual(
            ['name'],
            job_utils.find_possible_data_source_refs_by_name(job_configs))

        job_configs = {'args': ['first', id],
                       'configs': {'config': name_ref},
                       'params': {'param': 'value'}}
        self.assertEqual(
            ['name'],
            job_utils.find_possible_data_source_refs_by_name(job_configs))

        job_configs = {'args': ['first', id],
                       'configs': {'config': 'value'},
                       'params': {'param': name_ref}}
        self.assertEqual(
            ['name'],
            job_utils.find_possible_data_source_refs_by_name(job_configs))

        job_configs = {'args': [name_ref, name_ref2, id],
                       'configs': {'config': name_ref},
                       'params': {'param': name_ref}}
        self.assertItemsEqual(
            ['name', 'name2'],
            job_utils.find_possible_data_source_refs_by_name(job_configs))

    def test_find_possible_data_source_refs_by_uuid(self):
        job_configs = {}

        name_ref = job_utils.DATA_SOURCE_PREFIX+'name'

        self.assertEqual([],
                         job_utils.find_possible_data_source_refs_by_uuid(
                             job_configs))

        id = six.text_type(uuid.uuid4())
        job_configs = {'args': ['first', name_ref],
                       'configs': {'config': 'value'},
                       'params': {'param': 'value'}}
        self.assertEqual([],
                         job_utils.find_possible_data_source_refs_by_uuid(
                             job_configs))

        job_configs = {'args': [id, name_ref],
                       'configs': {'config': 'value'},
                       'params': {'param': 'value'}}
        self.assertEqual(
            [id],
            job_utils.find_possible_data_source_refs_by_uuid(job_configs))

        job_configs = {'args': ['first', name_ref],
                       'configs': {'config': id},
                       'params': {'param': 'value'}}
        self.assertEqual(
            [id],
            job_utils.find_possible_data_source_refs_by_uuid(job_configs))

        job_configs = {'args': ['first', name_ref],
                       'configs': {'config': 'value'},
                       'params': {'param': id}}
        self.assertEqual(
            [id],
            job_utils.find_possible_data_source_refs_by_uuid(job_configs))

        id2 = six.text_type(uuid.uuid4())
        job_configs = {'args': [id, id2, name_ref],
                       'configs': {'config': id},
                       'params': {'param': id}}
        self.assertItemsEqual([id, id2],
                              job_utils.find_possible_data_source_refs_by_uuid(
                                  job_configs))

    @mock.patch('sahara.context.ctx')
    @mock.patch('sahara.conductor.API.data_source_get_all')
    def test_resolve_data_source_refs(self, data_source_get_all, ctx):

        ctx.return_value = 'dummy'

        name_ref = job_utils.DATA_SOURCE_PREFIX+'input'
        job_exec_id = six.text_type(uuid.uuid4())

        input_url = "swift://container/input"
        input = u.create_data_source(input_url,
                                     name="input",
                                     id=six.text_type(uuid.uuid4()))

        output = u.create_data_source("swift://container/output.%JOB_EXEC_ID%",
                                      name="output",
                                      id=six.text_type(uuid.uuid4()))
        output_url = "swift://container/output." + job_exec_id

        by_name = {'input': input,
                   'output': output}

        by_id = {input.id: input,
                 output.id: output}

        # Pretend to be the database
        def _get_all(ctx, **kwargs):
            name = kwargs.get('name')
            if name in by_name:
                name_list = [by_name[name]]
            else:
                name_list = []

            id = kwargs.get('id')
            if id in by_id:
                id_list = [by_id[id]]
            else:
                id_list = []
            return list(set(name_list + id_list))

        data_source_get_all.side_effect = _get_all

        job_configs = {
            'configs': {
                job_utils.DATA_SOURCE_SUBST_NAME: True,
                job_utils.DATA_SOURCE_SUBST_UUID: True},
            'args': [name_ref, output.id, input.id]}
        urls = {}
        ds, nc = job_utils.resolve_data_source_references(job_configs,
                                                          job_exec_id, urls)
        self.assertEqual(2, len(ds))
        self.assertEqual([input.url, output_url, input.url], nc['args'])
        # Swift configs should be filled in since they were blank
        self.assertEqual(input.credentials['user'],
                         nc['configs']['fs.swift.service.sahara.username'])
        self.assertEqual(input.credentials['password'],
                         nc['configs']['fs.swift.service.sahara.password'])
        self.assertEqual(2, len(urls))
        self.assertItemsEqual({input.id: (input_url, input_url),
                               output.id: (output_url, output_url)}, urls)

        job_configs['configs'] = {'fs.swift.service.sahara.username': 'sam',
                                  'fs.swift.service.sahara.password': 'gamgee',
                                  job_utils.DATA_SOURCE_SUBST_NAME: False,
                                  job_utils.DATA_SOURCE_SUBST_UUID: True}
        ds, nc = job_utils.resolve_data_source_references(job_configs,
                                                          job_exec_id, {})
        self.assertEqual(2, len(ds))
        self.assertEqual([name_ref, output_url, input.url], nc['args'])
        # Swift configs should not be overwritten
        self.assertEqual(job_configs['configs'], nc['configs'])

        job_configs['configs'] = {job_utils.DATA_SOURCE_SUBST_NAME: True,
                                  job_utils.DATA_SOURCE_SUBST_UUID: False}
        job_configs['proxy_configs'] = {'proxy_username': 'john',
                                        'proxy_password': 'smith',
                                        'proxy_trust_id': 'trustme'}
        ds, nc = job_utils.resolve_data_source_references(job_configs,
                                                          job_exec_id, {})
        self.assertEqual(1, len(ds))
        self.assertEqual([input.url, output.id, input.id], nc['args'])

        # Swift configs should be empty and proxy configs should be preserved
        self.assertEqual(job_configs['configs'], nc['configs'])
        self.assertEqual(job_configs['proxy_configs'], nc['proxy_configs'])

        # Substitution not enabled
        job_configs['configs'] = {job_utils.DATA_SOURCE_SUBST_NAME: False,
                                  job_utils.DATA_SOURCE_SUBST_UUID: False}
        ds, nc = job_utils.resolve_data_source_references(job_configs,
                                                          job_exec_id, {})
        self.assertEqual(0, len(ds))
        self.assertEqual(job_configs['args'], nc['args'])
        self.assertEqual(job_configs['configs'], nc['configs'])

        # Substitution enabled but no values to modify
        job_configs['configs'] = {job_utils.DATA_SOURCE_SUBST_NAME: True,
                                  job_utils.DATA_SOURCE_SUBST_UUID: True}
        job_configs['args'] = ['val1', 'val2', 'val3']
        ds, nc = job_utils.resolve_data_source_references(job_configs,
                                                          job_exec_id, {})
        self.assertEqual(0, len(ds))
        self.assertEqual(nc['args'], job_configs['args'])
        self.assertEqual(nc['configs'], job_configs['configs'])

    def test_to_url_dict(self):
        data_source_urls = {'1': ('1_native', '1_runtime'),
                            '2': ('2_native', '2_runtime')}
        self.assertItemsEqual({'1': '1_native',
                               '2': '2_native'},
                              job_utils.to_url_dict(data_source_urls))

        self.assertItemsEqual({'1': '1_runtime',
                               '2': '2_runtime'},
                              job_utils.to_url_dict(data_source_urls,
                                                    runtime=True))

    def test_construct_data_source_url_no_placeholders(self):
        base_url = "swift://container/input"
        job_exec_id = six.text_type(uuid.uuid4())

        url = job_utils._construct_data_source_url(base_url, job_exec_id)

        self.assertEqual(base_url, url)

    def test_construct_data_source_url_job_exec_id_placeholder(self):
        base_url = "swift://container/input.%JOB_EXEC_ID%.out"
        job_exec_id = six.text_type(uuid.uuid4())

        url = job_utils._construct_data_source_url(base_url, job_exec_id)

        self.assertEqual(
            "swift://container/input." + job_exec_id + ".out", url)

    def test_construct_data_source_url_randstr_placeholder(self):
        base_url = "swift://container/input.%RANDSTR(4)%.%RANDSTR(7)%.out"
        job_exec_id = six.text_type(uuid.uuid4())

        url = job_utils._construct_data_source_url(base_url, job_exec_id)

        self.assertRegex(
            url, "swift://container/input\.[a-z]{4}\.[a-z]{7}\.out")
