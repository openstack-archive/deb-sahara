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

import logging
import telnetlib
import time

import fixtures
from keystoneclient.v2_0 import client as keystone_client
from neutronclient.v2_0 import client as neutron_client
from novaclient.v2 import client as nova_client
from oslo_utils import excutils
from oslo_utils import uuidutils
from oslotest import base
from saharaclient.api import base as client_base
import saharaclient.client as sahara_client
import six
from swiftclient import client as swift_client
from testtools import testcase

from sahara.tests.integration.configs import config as cfg
import sahara.utils.openstack.images as imgs
from sahara.utils import ssh_remote


logger = logging.getLogger('swiftclient')
logger.setLevel(logging.WARNING)


def errormsg(message):
    def decorator(fct):
        def wrapper(*args, **kwargs):
            try:
                fct(*args, **kwargs)
            except Exception as e:
                with excutils.save_and_reraise_exception():
                    ITestCase.print_error_log(message, e)

        return wrapper
    return decorator


def skip_test(config_name, message=''):
    def handle(func):
        def call(self, *args, **kwargs):
            if getattr(self, config_name):
                print(
                    '\n======================================================='
                )
                print('INFO: ' + message)
                print(
                    '=======================================================\n'
                )

            else:
                return func(self, *args, **kwargs)
        return call
    return handle


class ITestCase(testcase.WithAttributes, base.BaseTestCase):
    def setUp(self):
        super(ITestCase, self).setUp()
        self.common_config = cfg.ITConfig().common_config
        self.plugin_config = self.get_plugin_config()
        self._setup_clients()
        self._setup_networks()
        self._setup_volume_params()
        self._setup_flavor()
        self._setup_ssh_access()
        self.TEST_EVENT_LOG = True

        self._image_id, self._ssh_username = (
            self.get_image_id_and_ssh_username())

        telnetlib.Telnet(
            self.common_config.SAHARA_HOST, self.common_config.SAHARA_PORT
        )

    def get_plugin_config(self):
        raise NotImplementedError

    def _setup_ssh_access(self):
        if not self.common_config.PATH_TO_SSH_KEY:
            self.user_keypair_id = self.rand_name(
                self.common_config.USER_KEYPAIR_ID)
            self.private_key = self.nova.keypairs.create(
                self.user_keypair_id).private_key

        else:
            self.user_keypair_id = self.common_config.USER_KEYPAIR_ID
            self.private_key = open(self.common_config.PATH_TO_SSH_KEY).read()

    def _setup_flavor(self):
        if not self.common_config.FLAVOR_ID:
            self.flavor_id = self.nova.flavors.create(
                name=self.rand_name('i-test-flavor'),
                ram=1024,
                vcpus=1,
                disk=10,
                ephemeral=10).id

        else:
            self.flavor_id = self.common_config.FLAVOR_ID

    def _setup_networks(self):
        self.floating_ip_pool = self.common_config.FLOATING_IP_POOL
        self.internal_neutron_net = None
        if self.common_config.NEUTRON_ENABLED:
            self.internal_neutron_net = self.get_internal_neutron_net_id()
            self.floating_ip_pool = (
                self.get_floating_ip_pool_id_for_neutron_net())

    def _setup_volume_params(self):
        self.volumes_per_node = 0
        self.volumes_size = 0
        if not getattr(self.plugin_config, 'SKIP_CINDER_TEST', False):
            self.volumes_per_node = 2
            self.volumes_size = 2

    def _setup_clients(self):
        keystone = keystone_client.Client(
            username=self.common_config.OS_USERNAME,
            password=self.common_config.OS_PASSWORD,
            tenant_name=self.common_config.OS_TENANT_NAME,
            auth_url=self.common_config.OS_AUTH_URL)

        keystone.management_url = self.common_config.OS_AUTH_URL

        tenant_id = [tenant.id for tenant in keystone.tenants.list()
                     if tenant.name == self.common_config.OS_TENANT_NAME][0]

        self.sahara = sahara_client.Client(
            version=self.common_config.SAHARA_API_VERSION,
            username=self.common_config.OS_USERNAME,
            api_key=self.common_config.OS_PASSWORD,
            project_name=self.common_config.OS_TENANT_NAME,
            auth_url=self.common_config.OS_AUTH_URL,
            sahara_url='http://%s:%s/v%s/%s' % (
                self.common_config.SAHARA_HOST,
                self.common_config.SAHARA_PORT,
                self.common_config.SAHARA_API_VERSION,
                tenant_id
            ))

        self.nova = nova_client.Client(
            username=self.common_config.OS_USERNAME,
            api_key=self.common_config.OS_PASSWORD,
            project_id=self.common_config.OS_TENANT_NAME,
            auth_url=self.common_config.OS_AUTH_URL)

        self.neutron = neutron_client.Client(
            username=self.common_config.OS_USERNAME,
            password=self.common_config.OS_PASSWORD,
            tenant_name=self.common_config.OS_TENANT_NAME,
            auth_url=self.common_config.OS_AUTH_URL)

# ------------------------Methods for object creation--------------------------

    def create_node_group_template(self, name, plugin_config, description,
                                   node_processes, node_configs,
                                   volumes_per_node=0, volumes_size=0,
                                   floating_ip_pool=None, **kwargs):
        data = self.sahara.node_group_templates.create(
            name, plugin_config.PLUGIN_NAME, plugin_config.HADOOP_VERSION,
            self.flavor_id, description, volumes_per_node, volumes_size,
            node_processes, node_configs, floating_ip_pool, **kwargs)
        node_group_template_id = data.id
        return node_group_template_id

    def create_cluster_template(self, name, plugin_config, description,
                                cluster_configs, node_groups,
                                anti_affinity=None, net_id=None):
        for node_group in node_groups:
            for key, value in node_group.items():
                if value is None:
                    del node_group[key]
        data = self.sahara.cluster_templates.create(
            name, plugin_config.PLUGIN_NAME, plugin_config.HADOOP_VERSION,
            description, cluster_configs, node_groups, anti_affinity, net_id)
        cluster_template_id = data.id
        return cluster_template_id

    def create_cluster(self, name, plugin_config, cluster_template_id,
                       description, cluster_configs,
                       node_groups=None, anti_affinity=None,
                       net_id=None, is_transient=False):
        self.cluster_id = None

        data = self.sahara.clusters.create(
            name, plugin_config.PLUGIN_NAME, plugin_config.HADOOP_VERSION,
            cluster_template_id, self._image_id, is_transient,
            description, cluster_configs, node_groups,
            self.user_keypair_id, anti_affinity, net_id)
        self.cluster_id = data.id
        return self.cluster_id

    def get_cluster_info(self, plugin_config):
        node_ip_list_with_node_processes = (
            self.get_cluster_node_ip_list_with_node_processes(self.cluster_id))
        try:
            node_info = self.get_node_info(node_ip_list_with_node_processes,
                                           plugin_config)

        except Exception as e:
            with excutils.save_and_reraise_exception():
                print(
                    '\nFailure during check of node process deployment '
                    'on cluster node: ' + six.text_type(e)
                )

        # For example: method "create_cluster_and_get_info" return
        # {
        #       'node_info': {
        #               'tasktracker_count': 3,
        #               'node_count': 6,
        #               'namenode_ip': '172.18.168.242',
        #               'datanode_count': 3
        #               },
        #       'cluster_id': 'bee5c6a1-411a-4e88-95fc-d1fbdff2bb9d',
        #       'node_ip_list': {
        #               '172.18.168.153': ['tasktracker', 'datanode'],
        #               '172.18.168.208': ['secondarynamenode', 'oozie'],
        #               '172.18.168.93': ['tasktracker'],
        #               '172.18.168.101': ['tasktracker', 'datanode'],
        #               '172.18.168.242': ['namenode', 'jobtracker'],
        #               '172.18.168.167': ['datanode']
        #       },
        #       'plugin_config': <oslo_config.cfg.GroupAttr object at 0x215d9d>
        # }
        return {
            'cluster_id': self.cluster_id,
            'node_ip_list': node_ip_list_with_node_processes,
            'node_info': node_info,
            'plugin_config': plugin_config
        }

# --------Helper methods for cluster info obtaining and its processing---------

    def poll_cluster_state(self, cluster_id):
        data = self.sahara.clusters.get(cluster_id)
        timeout = self.common_config.CLUSTER_CREATION_TIMEOUT * 60

        try:
            with fixtures.Timeout(timeout, gentle=True):
                while True:
                    status = str(data.status)
                    if status == 'Active':
                        break
                    if status == 'Error':
                        self.fail('Cluster state == \'Error\'.')

                    time.sleep(10)
                    data = self.sahara.clusters.get(cluster_id)

        except fixtures.TimeoutException:
            self.fail("Cluster did not return to 'Active' state "
                      "within %d minutes." %
                      self.common_config.CLUSTER_CREATION_TIMEOUT)

        return status

    def get_cluster_node_ip_list_with_node_processes(self, cluster_id):
        data = self.sahara.clusters.get(cluster_id)
        node_groups = data.node_groups
        node_ip_list_with_node_processes = {}
        for node_group in node_groups:
            instances = node_group['instances']
            for instance in instances:
                node_ip = instance['management_ip']
                node_ip_list_with_node_processes[node_ip] = node_group[
                    'node_processes']
        # For example:
        # node_ip_list_with_node_processes = {
        #       '172.18.168.181': ['tasktracker'],
        #       '172.18.168.94': ['secondarynamenode'],
        #       '172.18.168.208': ['namenode', 'jobtracker'],
        #       '172.18.168.93': ['tasktracker', 'datanode'],
        #       '172.18.168.44': ['tasktracker', 'datanode'],
        #       '172.18.168.233': ['datanode']
        # }
        return node_ip_list_with_node_processes

    def put_file_to_hdfs(self, namenode_ip, remote_path, data):
        tmp_file_path = '/tmp/%s' % uuidutils.generate_uuid()[:8]
        self.open_ssh_connection(namenode_ip)
        self.write_file_to(tmp_file_path, data)
        self.execute_command(
            'sudo su - -c "hadoop dfs -copyFromLocal %s %s" %s' % (
                tmp_file_path, remote_path, self.plugin_config.HADOOP_USER))
        self.execute_command('rm -fr %s' % tmp_file_path)
        self.close_ssh_connection()

    def try_telnet(self, host, port):
        try:
            telnetlib.Telnet(host, port)

        except Exception as e:
            with excutils.save_and_reraise_exception():
                print(
                    '\nTelnet has failed: ' + six.text_type(e) +
                    '  NODE IP: %s, PORT: %s. Passed %s minute(s).'
                    % (host, port, self.common_config.TELNET_TIMEOUT)
                )

    def get_node_info(self, node_ip_list_with_node_processes, plugin_config):
        tasktracker_count = 0
        datanode_count = 0
        timeout = self.common_config.TELNET_TIMEOUT * 60
        with fixtures.Timeout(timeout, gentle=True):
            accessible = False
            proc_with_ports = plugin_config.HADOOP_PROCESSES_WITH_PORTS
            while not accessible:
                accessible = True
                for node_ip, processes in six.iteritems(
                        node_ip_list_with_node_processes):
                    try:
                        self.try_telnet(node_ip, '22')
                    except Exception:
                        accessible = False

                    for process in processes:
                        if process in proc_with_ports:
                            try:
                                self.try_telnet(node_ip,
                                                proc_with_ports[process])
                            except Exception:
                                print('Connection attempt. NODE PROCESS: %s, '
                                      'PORT: %s.' % (
                                          process, proc_with_ports[process]))
                                accessible = False

                if not accessible:
                    time.sleep(1)

        for node_ip, processes in six.iteritems(
                node_ip_list_with_node_processes):
            if plugin_config.PROCESS_NAMES['tt'] in processes:
                tasktracker_count += 1
            if plugin_config.PROCESS_NAMES['dn'] in processes:
                datanode_count += 1
            if plugin_config.PROCESS_NAMES['nn'] in processes:
                namenode_ip = node_ip

        return {
            'namenode_ip': namenode_ip,
            'tasktracker_count': tasktracker_count,
            'datanode_count': datanode_count,
            'node_count': len(node_ip_list_with_node_processes)
        }

    def await_active_workers_for_namenode(self, node_info, plugin_config):
        self.open_ssh_connection(node_info['namenode_ip'])
        timeout = self.common_config.HDFS_INITIALIZATION_TIMEOUT * 60
        try:
            with fixtures.Timeout(timeout, gentle=True):
                while True:
                    active_tasktracker_count = self.execute_command(
                        'sudo -u %s bash -lc "hadoop job -list-active-trackers'
                        '" | grep "^tracker_" | wc -l'
                        % plugin_config.HADOOP_USER)[1]
                    try:
                        active_tasktracker_count = int(
                            active_tasktracker_count)
                    except ValueError:
                        active_tasktracker_count = -1

                    active_datanode_count = self.execute_command(
                        'sudo -u %s bash -lc "hadoop dfsadmin -report" | '
                        'grep -e "Datanodes available:.*" '
                        '-e "Live datanodes.*" | grep -o "[0-9]*" | head -1'
                        % plugin_config.HADOOP_USER)[1]
                    try:
                        active_datanode_count = int(active_datanode_count)
                    except ValueError:
                        active_datanode_count = -1

                    if (active_tasktracker_count ==
                            node_info['tasktracker_count'] and
                            active_datanode_count ==
                            node_info['datanode_count']):
                        break

                    time.sleep(10)

        except fixtures.TimeoutException:
            self.fail(
                'Tasktracker or datanode cannot be started within '
                '%s minute(s) for namenode.'
                % self.common_config.HDFS_INITIALIZATION_TIMEOUT
            )
        finally:
            self.close_ssh_connection()

    def await_active_tasktracker(self, node_info, plugin_config):
        self.open_ssh_connection(node_info['namenode_ip'])
        for i in range(self.common_config.HDFS_INITIALIZATION_TIMEOUT * 6):
            time.sleep(10)
            active_tasktracker_count = self.execute_command(
                'sudo -u %s bash -lc "hadoop job -list-active-trackers" '
                '| grep "^tracker_" | wc -l'
                % plugin_config.HADOOP_USER)[1]
            active_tasktracker_count = int(active_tasktracker_count)
            if (active_tasktracker_count == node_info['tasktracker_count']):
                break
        else:
            self.fail(
                'Tasktracker or datanode cannot be started within '
                '%s minute(s) for namenode.'
                % self.common_config.HDFS_INITIALIZATION_TIMEOUT)
        self.close_ssh_connection()

    @skip_test('TEST_EVENT_LOG',
               'Testing event log was skipped until 0.7.8 client release')
    @errormsg("Failure while event log testing: ")
    def _test_event_log(self, cluster_id):
        cluster = self.sahara.clusters.get(cluster_id)
        events = self.sahara.events.list(cluster_id)

        invalid_steps = []
        if not events:
            events = []

        for step in cluster.provision_progress:
            if not step['successful']:
                invalid_steps.append(step)

        if len(invalid_steps) > 0 or len(events) > 0:
            events_info = "\n".join(six.text_type(e) for e in events)
            invalid_steps_info = "\n".join(six.text_type(e)
                                           for e in invalid_steps)
            steps_info = "\n".join(six.text_type(e)
                                   for e in cluster.provision_progress)
            self.fail(
                "Issues with event log work: "
                "\n Not removed events: \n\n {events}"
                "\n Incomplete steps: \n\n {invalid_steps}"
                "\n All steps: \n\n {steps}".format(
                    events=events_info,
                    steps=steps_info,
                    invalid_steps=invalid_steps_info))

# --------------------------------Remote---------------------------------------

    def connect_to_swift(self):
        return swift_client.Connection(
            authurl=self.common_config.OS_AUTH_URL,
            user=self.common_config.OS_USERNAME,
            key=self.common_config.OS_PASSWORD,
            tenant_name=self.common_config.OS_TENANT_NAME,
            auth_version=self.common_config.SWIFT_AUTH_VERSION
        )

    def open_ssh_connection(self, host):
        ssh_remote._connect(host, self._ssh_username, self.private_key)

    @staticmethod
    def execute_command(cmd):
        return ssh_remote._execute_command(cmd, get_stderr=True)

    @staticmethod
    def write_file_to(remote_file, data):
        ssh_remote._write_file_to(remote_file, data)

    @staticmethod
    def read_file_from(remote_file):
        return ssh_remote._read_file_from(remote_file)

    @staticmethod
    def close_ssh_connection():
        ssh_remote._cleanup()

    def transfer_helper_conf_file_to_node(self, file_name):
        file = open('sahara/tests/integration/tests/resources/%s' % file_name
                    ).read()
        try:
            self.write_file_to(file_name, file)

        except Exception as e:
            with excutils.save_and_reraise_exception():
                print(
                    '\nFailure while conf file transferring '
                    'to cluster node: ' + six.text_type(e)
                )

    def transfer_helper_script_to_node(self, script_name, parameter_list=None):
        script = open('sahara/tests/integration/tests/resources/%s'
                      % script_name).read()
        if parameter_list:
            for parameter, value in parameter_list.items():
                script = script.replace(
                    '%s=""' % parameter, '%s=%s' % (parameter, value))
        try:
            self.write_file_to('script.sh', script)

        except Exception as e:
            with excutils.save_and_reraise_exception():
                print(
                    '\nFailure while helper script transferring '
                    'to cluster node: ' + six.text_type(e)
                )
        self.execute_command('chmod 777 script.sh')

    def transfer_helper_script_to_nodes(self, node_ip_list, script_name,
                                        parameter_list=None):
        for node_ip in node_ip_list:
            self.open_ssh_connection(node_ip)
            self.transfer_helper_script_to_node(script_name, parameter_list)
            self.close_ssh_connection()

# -------------------------------Helper methods--------------------------------

    def get_image_id_and_ssh_username(self):
        def print_error_log(parameter, value):
            print(
                '\nImage with %s "%s" was found in image list but it was '
                'possibly not registered for Sahara. Please, make sure image '
                'was correctly registered.' % (parameter, value)
            )

        def try_get_image_id_and_ssh_username(parameter, value):
            try:
                return image.id, image.metadata[imgs.PROP_USERNAME]

            except KeyError:
                with excutils.save_and_reraise_exception():
                    print_error_log(parameter, value)

        images = self.nova.images.list()
        # If plugin_config.IMAGE_ID is not None then find corresponding image
        # and return its ID and username. If image not found then handle error
        if self.plugin_config.IMAGE_ID:
            for image in images:
                if image.id == self.plugin_config.IMAGE_ID:
                    return try_get_image_id_and_ssh_username(
                        'ID', self.plugin_config.IMAGE_ID)
            self.fail(
                '\n\nImage with ID "%s" not found in image list. Please, make '
                'sure you specified right image ID.\n' %
                self.plugin_config.IMAGE_ID)
        # If plugin_config.IMAGE_NAME is not None then find corresponding image
        # and return its ID and username. If image not found then handle error
        if self.plugin_config.IMAGE_NAME:
            for image in images:
                if image.name == self.plugin_config.IMAGE_NAME:
                    return try_get_image_id_and_ssh_username(
                        'name', self.plugin_config.IMAGE_NAME)
            self.fail(
                '\n\nImage with name "%s" not found in image list. Please, '
                'make sure you specified right image name.\n'
                % self.plugin_config.IMAGE_NAME)
        # If plugin_config.IMAGE_TAG is not None then find corresponding image
        # and return its ID and username. If image not found then handle error
        if self.plugin_config.IMAGE_TAG:
            for image in images:
                if (image.metadata.get(imgs.PROP_TAG + '%s'
                    % self.plugin_config.IMAGE_TAG)) and (
                        image.metadata.get(imgs.PROP_TAG + str(
                                           self.plugin_config.PLUGIN_NAME))):
                    return try_get_image_id_and_ssh_username(
                        'tag', self.plugin_config.IMAGE_TAG
                    )
            self.fail(
                '\n\nImage with tag "%s" not found in list of registered '
                'images for Sahara. Please, make sure tag "%s" was added to '
                'image and image was correctly registered.\n'
                % (self.plugin_config.IMAGE_TAG, self.plugin_config.IMAGE_TAG)
            )
        # If plugin_config.IMAGE_ID, plugin_config.IMAGE_NAME and
        # plugin_config.IMAGE_TAG are None then image is chosen
        # by tag "sahara_i_tests". If image has tag "sahara_i_tests"
        # (at the same time image ID, image name and image tag were not
        # specified in configuration file of integration tests) then return
        # its ID and username. Found image will be chosen as image for tests.
        # If image with tag "sahara_i_tests" not found then handle error
        for image in images:
            if (image.metadata.get(imgs.PROP_TAG + 'sahara_i_tests')) and (
                    image.metadata.get(imgs.PROP_TAG + str(
                                       self.plugin_config.PLUGIN_NAME))):
                try:
                    return image.id, image.metadata[imgs.PROP_USERNAME]

                except KeyError:
                        with excutils.save_and_reraise_exception():
                            print(
                                '\nNone of parameters of image (ID, name, tag)'
                                ' was specified in configuration file of '
                                'integration tests. That is why there was '
                                'attempt to choose image by tag '
                                '"sahara_i_tests" and image with such tag '
                                'was found in image list but it was possibly '
                                'not registered for Sahara. Please, make '
                                'sure image was correctly registered.'
                            )
        self.fail(
            '\n\nNone of parameters of image (ID, name, tag) was specified in '
            'configuration file of integration tests. That is why there was '
            'attempt to choose image by tag "sahara_i_tests" but image with '
            'such tag not found in list of registered images for Sahara. '
            'Please, make sure image was correctly registered. Please, '
            'specify one of parameters of image (ID, name or tag) in '
            'configuration file of integration tests.\n'
        )

    def get_floating_ip_pool_id_for_neutron_net(self):
        # Find corresponding floating IP pool by its name and get its ID.
        # If pool not found then handle error
        try:
            floating_ip_pool = self.neutron.list_networks(
                name=self.common_config.FLOATING_IP_POOL)
            floating_ip_pool_id = floating_ip_pool['networks'][0]['id']
            return floating_ip_pool_id

        except IndexError:
            with excutils.save_and_reraise_exception():
                raise Exception(
                    '\nFloating IP pool \'%s\' not found in pool list. '
                    'Please, make sure you specified right floating IP pool.'
                    % self.common_config.FLOATING_IP_POOL
                )

    def get_internal_neutron_net_id(self):
        # Find corresponding internal Neutron network by its name and get
        # its ID. If network not found then handle error
        try:
            internal_neutron_net = self.neutron.list_networks(
                name=self.common_config.INTERNAL_NEUTRON_NETWORK)
            internal_neutron_net_id = internal_neutron_net['networks'][0]['id']
            return internal_neutron_net_id

        except IndexError:
            with excutils.save_and_reraise_exception():
                raise Exception(
                    '\nInternal Neutron network \'%s\' not found in network '
                    'list. Please, make sure you specified right network name.'
                    % self.common_config.INTERNAL_NEUTRON_NETWORK
                )

    def delete_cluster(self, cluster_id):
        if not self.common_config.RETAIN_CLUSTER_AFTER_TEST:
            return self.delete_resource(self.sahara.clusters.delete,
                                        cluster_id)

    def delete_cluster_template(self, cluster_template_id):
        if not self.common_config.RETAIN_CLUSTER_AFTER_TEST:
            return self.delete_resource(self.sahara.cluster_templates.delete,
                                        cluster_template_id)

    def delete_node_group_template(self, node_group_template_id):
        if not self.common_config.RETAIN_CLUSTER_AFTER_TEST:
            return self.delete_resource(
                self.sahara.node_group_templates.delete,
                node_group_template_id)

    def is_resource_deleted(self, method, *args, **kwargs):
        try:
            method(*args, **kwargs)
        except client_base.APIException as ex:
            return ex.error_code == 404

        return False

    def delete_resource(self, method, *args, **kwargs):
        with fixtures.Timeout(self.common_config.DELETE_RESOURCE_TIMEOUT*60,
                              gentle=True):
            while True:
                if self.is_resource_deleted(method, *args, **kwargs):
                    break
                time.sleep(5)

    @staticmethod
    def delete_swift_container(swift, container):
        objects = [obj['name'] for obj in swift.get_container(container)[1]]
        for obj in objects:
            swift.delete_object(container, obj)
        swift.delete_container(container)

    @staticmethod
    def print_error_log(message, exception=None):
        print(
            '\n\n!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!* '
            'ERROR LOG *!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*'
            '!*!\n'
        )
        print(message + six.text_type(exception))
        print(
            '\n!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!* END OF '
            'ERROR LOG *!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*'
            '!*!\n\n'
        )

    def capture_error_log_from_cluster_node(self, log_file):
        print(
            '\n\n!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!* CAPTURED ERROR '
            'LOG FROM CLUSTER NODE *!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*'
            '!*!\n'
        )
        print(self.read_file_from(log_file))
        print(
            '\n!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!* END OF CAPTURED ERROR '
            'LOG FROM CLUSTER NODE *!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*!*'
            '!*!\n\n'
        )

    @staticmethod
    def rand_name(name):
        return '%s-%s' % (name, uuidutils.generate_uuid()[:8])

    def tearDown(self):
        if not self.common_config.PATH_TO_SSH_KEY:
            self.nova.keypairs.delete(self.user_keypair_id)
        if not self.common_config.FLAVOR_ID:
            self.nova.flavors.delete(self.flavor_id)

        super(ITestCase, self).tearDown()
