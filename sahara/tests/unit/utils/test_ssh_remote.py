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

import shlex

import mock
import testtools

from sahara import exceptions as ex
from sahara.tests.unit import base
from sahara.utils import ssh_remote


class TestEscapeQuotes(testtools.TestCase):
    def test_escape_quotes(self):
        s = ssh_remote._escape_quotes('echo "\\"Hello, world!\\""')
        self.assertEqual(r'echo \"\\\"Hello, world!\\\"\"', s)


class FakeCluster(object):
    def __init__(self, priv_key):
        self.management_private_key = priv_key
        self.neutron_management_network = 'network1'

    def has_proxy_gateway(self):
        return False

    def get_proxy_gateway_node(self):
        return None


class FakeNodeGroup(object):
    def __init__(self, user, priv_key):
        self.image_username = user
        self.cluster = FakeCluster(priv_key)


class FakeInstance(object):
    def __init__(self, inst_name, management_ip, user, priv_key):
        self.instance_name = inst_name
        self.management_ip = management_ip
        self.node_group = FakeNodeGroup(user, priv_key)

    @property
    def cluster(self):
        return self.node_group.cluster


class TestInstanceInteropHelper(base.SaharaTestCase):
    def setUp(self):
        super(TestInstanceInteropHelper, self).setUp()

        p_sma = mock.patch('sahara.utils.ssh_remote._acquire_remote_semaphore')
        p_sma.start()
        p_smr = mock.patch('sahara.utils.ssh_remote._release_remote_semaphore')
        p_smr.start()

        p_neutron_router = mock.patch(
            'sahara.utils.openstack.neutron.NeutronClient.get_router',
            return_value='fakerouter')
        p_neutron_router.start()

        # During tests subprocesses are not used (because _sahara-subprocess
        # is not installed in /bin and Mock objects cannot be pickled).
        p_start_subp = mock.patch('sahara.utils.procutils.start_subprocess',
                                  return_value=42)
        p_start_subp.start()
        p_run_subp = mock.patch('sahara.utils.procutils.run_in_subprocess')
        self.run_in_subprocess = p_run_subp.start()
        p_shut_subp = mock.patch('sahara.utils.procutils.shutdown_subprocess')
        p_shut_subp.start()

        self.patchers = [p_sma, p_smr, p_neutron_router, p_start_subp,
                         p_run_subp, p_shut_subp]

    def tearDown(self):
        for patcher in self.patchers:
            patcher.stop()
        super(TestInstanceInteropHelper, self).tearDown()

    def setup_context(self, username="test_user", tenant_id="tenant_1",
                      token="test_auth_token", tenant_name='test_tenant',
                      **kwargs):
        service_catalog = '''[
            { "type": "network",
              "endpoints": [ { "region": "RegionOne",
                               "publicURL": "http://localhost/" } ] } ]'''
        super(TestInstanceInteropHelper, self).setup_context(
            username=username, tenant_id=tenant_id, token=token,
            tenant_name=tenant_name, service_catalog=service_catalog, **kwargs)

    # When use_floating_ips=True, no proxy should be used: _connect is called
    # with proxy=None and ProxiedHTTPAdapter is not used.
    @mock.patch('sahara.utils.ssh_remote.ProxiedHTTPAdapter')
    def test_use_floating_ips(self, p_adapter):
        self.override_config('use_floating_ips', True)

        instance = FakeInstance('inst1', '10.0.0.1', 'user1', 'key1')
        remote = ssh_remote.InstanceInteropHelper(instance)

        # Test SSH
        remote.execute_command('/bin/true')
        self.run_in_subprocess.assert_any_call(
            42, ssh_remote._connect, ('10.0.0.1', 'user1', 'key1',
                                      None, None, None))
        # Test HTTP
        remote.get_http_client(8080)
        self.assertFalse(p_adapter.called)

    # When use_floating_ips=False and use_namespaces=True, a netcat socket
    # created with 'ip netns exec qrouter-...' should be used to access
    # instances.
    @mock.patch('sahara.utils.ssh_remote._simple_exec_func')
    @mock.patch('sahara.utils.ssh_remote.ProxiedHTTPAdapter')
    def test_use_namespaces(self, p_adapter, p_simple_exec_func):
        self.override_config('use_floating_ips', False)
        self.override_config('use_namespaces', True)

        instance = FakeInstance('inst2', '10.0.0.2', 'user2', 'key2')
        remote = ssh_remote.InstanceInteropHelper(instance)

        # Test SSH
        remote.execute_command('/bin/true')
        self.run_in_subprocess.assert_any_call(
            42, ssh_remote._connect,
            ('10.0.0.2', 'user2', 'key2',
             'ip netns exec qrouter-fakerouter nc 10.0.0.2 22', None, None))
        # Test HTTP
        remote.get_http_client(8080)
        p_adapter.assert_called_once_with(
            p_simple_exec_func(),
            '10.0.0.2', 8080)
        p_simple_exec_func.assert_any_call(
            shlex.split('ip netns exec qrouter-fakerouter nc 10.0.0.2 8080'))

    # When proxy_command is set, a user-defined netcat socket should be used to
    # access instances.
    @mock.patch('sahara.utils.ssh_remote._simple_exec_func')
    @mock.patch('sahara.utils.ssh_remote.ProxiedHTTPAdapter')
    def test_proxy_command(self, p_adapter, p_simple_exec_func):
        self.override_config('proxy_command', 'ssh fakerelay nc {host} {port}')

        instance = FakeInstance('inst3', '10.0.0.3', 'user3', 'key3')
        remote = ssh_remote.InstanceInteropHelper(instance)

        # Test SSH
        remote.execute_command('/bin/true')
        self.run_in_subprocess.assert_any_call(
            42, ssh_remote._connect,
            ('10.0.0.3', 'user3', 'key3', 'ssh fakerelay nc 10.0.0.3 22',
             None, None))
        # Test HTTP
        remote.get_http_client(8080)
        p_adapter.assert_called_once_with(
            p_simple_exec_func(), '10.0.0.3', 8080)
        p_simple_exec_func.assert_any_call(
            shlex.split('ssh fakerelay nc 10.0.0.3 8080'))

    def test_proxy_command_bad(self):
        self.override_config('proxy_command', '{bad_kw} nc {host} {port}')

        instance = FakeInstance('inst4', '10.0.0.4', 'user4', 'key4')
        remote = ssh_remote.InstanceInteropHelper(instance)

        # Test SSH
        self.assertRaises(ex.SystemError, remote.execute_command, '/bin/true')
        # Test HTTP
        self.assertRaises(ex.SystemError, remote.get_http_client, 8080)
