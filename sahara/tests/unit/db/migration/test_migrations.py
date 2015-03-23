# Copyright 2014 OpenStack Foundation
# Copyright 2014 Mirantis Inc
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""
Tests for database migrations.

For the opportunistic testing you need to set up a db named 'openstack_citest'
with user 'openstack_citest' and password 'openstack_citest' on localhost.
The test will then use that db and u/p combo to run the tests.

For postgres on Ubuntu this can be done with the following commands:

sudo -u postgres psql
postgres=# create user openstack_citest with createdb login password
      'openstack_citest';
postgres=# create database openstack_citest with owner openstack_citest;

"""

import os

from oslo_db.sqlalchemy import test_base
from oslo_db.sqlalchemy import utils as db_utils

from sahara.tests.unit.db.migration import test_migrations_base as base


class SaharaMigrationsCheckers(object):

    snake_walk = True
    downgrade = True

    def assertColumnExists(self, engine, table, column):
        t = db_utils.get_table(engine, table)
        self.assertIn(column, t.c)

    def assertColumnsExists(self, engine, table, columns):
        for column in columns:
            self.assertColumnExists(engine, table, column)

    def assertColumnCount(self, engine, table, columns):
        t = db_utils.get_table(engine, table)
        self.assertEqual(len(t.columns), len(columns))

    def assertColumnNotExists(self, engine, table, column):
        t = db_utils.get_table(engine, table)
        self.assertNotIn(column, t.c)

    def assertIndexExists(self, engine, table, index):
        t = db_utils.get_table(engine, table)
        index_names = [idx.name for idx in t.indexes]
        self.assertIn(index, index_names)

    def assertIndexMembers(self, engine, table, index, members):
        self.assertIndexExists(engine, table, index)

        t = db_utils.get_table(engine, table)
        index_columns = None
        for idx in t.indexes:
            if idx.name == index:
                index_columns = idx.columns.keys()
                break

        self.assertEqual(sorted(members), sorted(index_columns))

    def test_walk_versions(self):
        self.walk_versions(self.engine, self.snake_walk, self.downgrade)

    def _pre_upgrade_001(self, engine):
        # Anything returned from this method will be
        # passed to corresponding _check_xxx method as 'data'.
        pass

    def _check_001(self, engine, data):
        job_binary_internal_columns = [
            'created_at',
            'updated_at',
            'id',
            'tenant_id',
            'name',
            'data',
            'datasize'
        ]
        self.assertColumnsExists(
            engine, 'job_binary_internal', job_binary_internal_columns)
        self.assertColumnCount(
            engine, 'job_binary_internal', job_binary_internal_columns)

        node_group_templates_columns = [
            'created_at',
            'updated_at',
            'id',
            'name',
            'description',
            'tenant_id',
            'flavor_id',
            'image_id',
            'plugin_name',
            'hadoop_version',
            'node_processes',
            'node_configs',
            'volumes_per_node',
            'volumes_size',
            'volume_mount_prefix',
            'floating_ip_pool'
        ]
        self.assertColumnsExists(
            engine, 'node_group_templates', node_group_templates_columns)
        self.assertColumnCount(
            engine, 'node_group_templates', node_group_templates_columns)

        data_sources_columns = [
            'created_at',
            'updated_at',
            'id',
            'tenant_id',
            'name',
            'description',
            'type',
            'url',
            'credentials'
        ]
        self.assertColumnsExists(
            engine, 'data_sources', data_sources_columns)
        self.assertColumnCount(
            engine, 'data_sources', data_sources_columns)

        cluster_templates_columns = [
            'created_at',
            'updated_at',
            'id',
            'name',
            'description',
            'cluster_configs',
            'default_image_id',
            'anti_affinity',
            'tenant_id',
            'neutron_management_network',
            'plugin_name',
            'hadoop_version'
        ]
        self.assertColumnsExists(
            engine, 'cluster_templates', cluster_templates_columns)
        self.assertColumnCount(
            engine, 'cluster_templates', cluster_templates_columns)

        job_binaries_columns = [
            'created_at',
            'updated_at',
            'id',
            'tenant_id',
            'name',
            'description',
            'url',
            'extra'
        ]
        self.assertColumnsExists(
            engine, 'job_binaries', job_binaries_columns)
        self.assertColumnCount(
            engine, 'job_binaries', job_binaries_columns)

        jobs_columns = [
            'created_at',
            'updated_at',
            'id',
            'tenant_id',
            'name',
            'description',
            'type'
        ]
        self.assertColumnsExists(engine, 'jobs', jobs_columns)
        self.assertColumnCount(engine, 'jobs', jobs_columns)

        templates_relations_columns = [
            'created_at',
            'updated_at',
            'id',
            'tenant_id',
            'name',
            'flavor_id',
            'image_id',
            'node_processes',
            'node_configs',
            'volumes_per_node',
            'volumes_size',
            'volume_mount_prefix',
            'count',
            'cluster_template_id',
            'node_group_template_id',
            'floating_ip_pool'
        ]
        self.assertColumnsExists(
            engine, 'templates_relations', templates_relations_columns)
        self.assertColumnCount(
            engine, 'templates_relations', templates_relations_columns)

        mains_association_columns = [
            'Job_id',
            'JobBinary_id'
        ]
        self.assertColumnsExists(
            engine, 'mains_association', mains_association_columns)
        self.assertColumnCount(
            engine, 'mains_association', mains_association_columns)

        libs_association_columns = [
            'Job_id',
            'JobBinary_id'
        ]
        self.assertColumnsExists(
            engine, 'libs_association', libs_association_columns)
        self.assertColumnCount(
            engine, 'libs_association', libs_association_columns)

        clusters_columns = [
            'created_at',
            'updated_at',
            'id',
            'name',
            'description',
            'tenant_id',
            'trust_id',
            'is_transient',
            'plugin_name',
            'hadoop_version',
            'cluster_configs',
            'default_image_id',
            'neutron_management_network',
            'anti_affinity',
            'management_private_key',
            'management_public_key',
            'user_keypair_id',
            'status',
            'status_description',
            'info',
            'extra',
            'cluster_template_id'
        ]
        self.assertColumnsExists(engine, 'clusters', clusters_columns)
        self.assertColumnCount(engine, 'clusters', clusters_columns)

        node_groups_columns = [
            'created_at',
            'updated_at',
            'id',
            'name',
            'tenant_id',
            'flavor_id',
            'image_id',
            'image_username',
            'node_processes',
            'node_configs',
            'volumes_per_node',
            'volumes_size',
            'volume_mount_prefix',
            'count',
            'cluster_id',
            'node_group_template_id',
            'floating_ip_pool'
        ]
        self.assertColumnsExists(engine, 'node_groups', node_groups_columns)
        self.assertColumnCount(engine, 'node_groups', node_groups_columns)

        job_executions_columns = [
            'created_at',
            'updated_at',
            'id',
            'tenant_id',
            'job_id',
            'input_id',
            'output_id',
            'start_time',
            'end_time',
            'cluster_id',
            'info',
            'progress',
            'oozie_job_id',
            'return_code',
            'job_configs',
            'extra'
        ]
        self.assertColumnsExists(
            engine, 'job_executions', job_executions_columns)
        self.assertColumnCount(
            engine, 'job_executions', job_executions_columns)

        instances_columns = [
            'created_at',
            'updated_at',
            'id',
            'tenant_id',
            'node_group_id',
            'instance_id',
            'instance_name',
            'internal_ip',
            'management_ip',
            'volumes'
        ]
        self.assertColumnsExists(engine, 'instances', instances_columns)
        self.assertColumnCount(engine, 'instances', instances_columns)

        self._data_001(engine, data)

    def _data_001(self, engine, data):
        datasize = 512 * 1024  # 512kB
        data = os.urandom(datasize)
        t = db_utils.get_table(engine, 'job_binary_internal')
        engine.execute(t.insert(), data=data, id='123', name='name')
        new_data = engine.execute(t.select()).fetchone().data
        self.assertEqual(data, new_data)
        engine.execute(t.delete())

    def _check_002(self, engine, data):
        # currently, 002 is just a placeholder
        pass

    def _check_003(self, engine, data):
        # currently, 003 is just a placeholder
        pass

    def _check_004(self, engine, data):
        # currently, 004 is just a placeholder
        pass

    def _check_005(self, engine, data):
        # currently, 005 is just a placeholder
        pass

    def _check_006(self, engine, data):
        # currently, 006 is just a placeholder
        pass

    def _pre_upgrade_007(self, engine):
        desc = 'magic'
        t = db_utils.get_table(engine, 'clusters')
        engine.execute(t.insert(), id='123', name='name', plugin_name='pname',
                       hadoop_version='1',  management_private_key='2',
                       management_public_key='3', status_description=desc)

    def _check_007(self, engine, data):
        t = db_utils.get_table(engine, 'clusters')
        res = engine.execute(t.select(), id='123').first()
        self.assertEqual('magic', res['status_description'])
        engine.execute(t.delete())

        # check that status_description can keep 128kb.
        # MySQL varchar can not keep more then 64kb
        desc = 'a' * 128 * 1024  # 128kb
        t = db_utils.get_table(engine, 'clusters')
        engine.execute(t.insert(), id='123', name='name', plugin_name='plname',
                       hadoop_version='hversion', management_private_key='1',
                       management_public_key='2', status_description=desc)
        new_desc = engine.execute(t.select()).fetchone().status_description
        self.assertEqual(desc, new_desc)
        engine.execute(t.delete())

    def _check_008(self, engine, data):
        self.assertColumnExists(engine, 'node_group_templates',
                                'security_groups')
        self.assertColumnExists(engine, 'node_groups', 'security_groups')
        self.assertColumnExists(engine, 'templates_relations',
                                'security_groups')

    def _check_009(self, engine, data):
        self.assertColumnExists(engine, 'clusters', 'rollback_info')

    def _check_010(self, engine, data):
        self.assertColumnExists(engine, 'node_group_templates',
                                'auto_security_group')
        self.assertColumnExists(engine, 'node_groups', 'auto_security_group')
        self.assertColumnExists(engine, 'templates_relations',
                                'auto_security_group')
        self.assertColumnExists(engine, 'node_groups', 'open_ports')

    def _check_011(self, engine, data):
        self.assertColumnExists(engine, 'clusters', 'sahara_info')

    def _check_012(self, engine, data):
        self.assertColumnExists(engine, 'node_group_templates',
                                'availability_zone')
        self.assertColumnExists(engine, 'node_groups', 'availability_zone')
        self.assertColumnExists(engine, 'templates_relations',
                                'availability_zone')

    def _check_014(self, engine, data):
        self.assertColumnExists(engine, 'node_group_templates', 'volume_type')
        self.assertColumnExists(engine, 'node_groups', 'volume_type')
        self.assertColumnExists(engine, 'templates_relations', 'volume_type')

    def _check_015(self, engine, data):
        provision_steps_columns = [
            'created_at',
            'updated_at',
            'id',
            'cluster_id',
            'tenant_id',
            'step_name',
            'step_type',
            'completed',
            'total',
            'successful',
            'started_at',
            'completed_at',
        ]
        events_columns = [
            'created_at',
            'updated_at',
            'id',
            'node_group_id',
            'instance_id',
            'instance_name',
            'event_info',
            'successful',
            'step_id',
        ]

        self.assertColumnCount(engine, 'cluster_provision_steps',
                               provision_steps_columns)
        self.assertColumnsExists(engine, 'cluster_provision_steps',
                                 provision_steps_columns)

        self.assertColumnCount(engine, 'cluster_events', events_columns)
        self.assertColumnsExists(engine, 'cluster_events', events_columns)

    def _check_016(self, engine, data):
        self.assertColumnExists(engine, 'node_group_templates',
                                'is_proxy_gateway')
        self.assertColumnExists(engine, 'node_groups', 'is_proxy_gateway')
        self.assertColumnExists(engine, 'templates_relations',
                                'is_proxy_gateway')

    def _check_017(self, engine, data):
        self.assertColumnNotExists(engine, 'job_executions', 'progress')

    def _check_018(self, engine, data):
        self.assertColumnExists(engine, 'node_group_templates',
                                'volume_local_to_instance')
        self.assertColumnExists(engine, 'node_groups',
                                'volume_local_to_instance')
        self.assertColumnExists(engine, 'templates_relations',
                                'volume_local_to_instance')

    def _check_019(self, engine, data):
        self.assertColumnExists(engine, 'node_group_templates', 'is_default')
        self.assertColumnExists(engine, 'cluster_templates', 'is_default')

    def _check_020(self, engine, data):
        self.assertColumnNotExists(engine, 'cluster_provision_steps',
                                   'completed')
        self.assertColumnNotExists(engine, 'cluster_provision_steps',
                                   'completed_at')
        self.assertColumnNotExists(engine, 'cluster_provision_steps',
                                   'started_at')


class TestMigrationsMySQL(SaharaMigrationsCheckers,
                          base.BaseWalkMigrationTestCase,
                          base.TestModelsMigrationsSync,
                          test_base.MySQLOpportunisticTestCase):
    pass


class TestMigrationsPostgresql(SaharaMigrationsCheckers,
                               base.BaseWalkMigrationTestCase,
                               base.TestModelsMigrationsSync,
                               test_base.PostgreSQLOpportunisticTestCase):
    pass
