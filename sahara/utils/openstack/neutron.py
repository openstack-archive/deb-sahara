# Copyright (c) 2013 Hortonworks, Inc.
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


from neutronclient.neutron import client as neutron_cli

from sahara import context
from sahara import exceptions as ex
from sahara.i18n import _
from sahara.openstack.common import log as logging
from sahara.utils.openstack import base


LOG = logging.getLogger(__name__)


def client():
    ctx = context.ctx()
    args = {
        'username': ctx.username,
        'tenant_name': ctx.tenant_name,
        'tenant_id': ctx.tenant_id,
        'token': ctx.auth_token,
        'endpoint_url': base.url_for(ctx.service_catalog, 'network')
    }
    return neutron_cli.Client('2.0', **args)


class NeutronClient(object):
    neutron = None
    routers = {}

    def __init__(self, network, uri, token, tenant_name):
        self.neutron = neutron_cli.Client('2.0',
                                          endpoint_url=uri,
                                          token=token,
                                          tenant_name=tenant_name)
        self.network = network

    def get_router(self):
        matching_router = NeutronClient.routers.get(self.network, None)
        if matching_router:
            LOG.debug('Returning cached qrouter')
            return matching_router['id']

        routers = self.neutron.list_routers()['routers']
        for router in routers:
            device_id = router['id']
            ports = self.neutron.list_ports(device_id=device_id)['ports']
            port = next((port for port in ports
                         if port['network_id'] == self.network), None)
            if port:
                matching_router = router
                NeutronClient.routers[self.network] = matching_router
                break

        if not matching_router:
            raise ex.SystemError(_('Neutron router corresponding to network '
                                   '%s is not found') % self.network)

        return matching_router['id']


def get_private_network_cidrs(cluster):
    neutron_client = client()
    private_net = neutron_client.show_network(
        cluster.neutron_management_network)

    cidrs = []
    for subnet_id in private_net['network']['subnets']:
        subnet = neutron_client.show_subnet(subnet_id)
        cidrs.append(subnet['subnet']['cidr'])

    return cidrs
