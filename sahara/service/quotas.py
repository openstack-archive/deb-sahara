# Copyright (c) 2015 Mirantis Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from oslo_config import cfg
import six

from sahara import context
from sahara import exceptions as ex
from sahara.i18n import _
from sahara.utils.openstack import cinder as cinder_client
from sahara.utils.openstack import neutron as neutron_client
from sahara.utils.openstack import nova as nova_client

CONF = cfg.CONF


def _get_zero_limits():
    return {
        'ram': 0,
        'cpu': 0,
        'instances': 0,
        'floatingips': 0,
        'security_groups': 0,
        'security_group_rules': 0,
        'ports': 0,
        'volumes': 0,
        'volume_gbs': 0
    }


def check_cluster(cluster):
    req_limits = _get_req_cluster_limits(cluster)
    _check_limits(req_limits)


def check_scaling(cluster, to_be_enlarged, additional):
    req_limits = _get_req_scaling_limits(cluster, to_be_enlarged, additional)
    _check_limits(req_limits)


def _check_limits(req_limits):
    limits_name_map = {
        'ram': _("RAM"),
        'cpu': _("VCPU"),
        'instances': _("instance"),
        'floatingips': _("floating ip"),
        'security_groups': _("security group"),
        'security_group_rules': _("security group rule"),
        'ports': _("port"),
        'volumes': _("volume"),
        'volume_gbs': _("volume storage")
    }

    avail_limits = _get_avail_limits()
    for quota, quota_name in six.iteritems(limits_name_map):
        if avail_limits[quota] < req_limits[quota]:
            raise ex.QuotaException(quota_name, req_limits[quota],
                                    avail_limits[quota])


def _get_req_cluster_limits(cluster):
    req_limits = _get_zero_limits()
    for ng in cluster.node_groups:
        _update_limits_for_ng(req_limits, ng, ng.count)
    return req_limits


def _get_req_scaling_limits(cluster, to_be_enlarged, additional):
    ng_id_map = to_be_enlarged.copy()
    ng_id_map.update(additional)
    req_limits = _get_zero_limits()
    for ng in cluster.node_groups:
        if ng_id_map.get(ng.id):
            _update_limits_for_ng(req_limits, ng, ng_id_map[ng.id] - ng.count)
    return req_limits


def _update_limits_for_ng(limits, ng, count):
    sign = lambda x: (1, -1)[x < 0]
    nova = nova_client.client()
    limits['instances'] += count
    flavor = nova.flavors.get(ng.flavor_id)
    limits['ram'] += flavor.ram * count
    limits['cpu'] += flavor.vcpus * count
    if ng.floating_ip_pool:
        limits['floatingips'] += count
    if ng.volumes_per_node:
        limits['volumes'] += ng.volumes_per_node * count
        limits['volume_gbs'] += ng.volumes_per_node * ng.volumes_size * count
    if ng.auto_security_group:
        limits['security_groups'] += sign(count)
        # NOTE: +3 - all traffic for private network
        if CONF.use_neutron:
            limits['security_group_rules'] += (
                (len(ng.open_ports) + 3) * sign(count))
        else:
            limits['security_group_rules'] = max(
                limits['security_group_rules'], len(ng.open_ports) + 3)
    if CONF.use_neutron:
        limits['ports'] += count


def _get_avail_limits():
    limits = _get_zero_limits()
    limits.update(_get_nova_limits())
    limits.update(_get_neutron_limits())
    limits.update(_get_cinder_limits())
    return limits


def _get_nova_limits():
    limits = {}
    nova = nova_client.client()
    lim = nova.limits.get().to_dict()['absolute']
    limits['ram'] = lim['maxTotalRAMSize'] - lim['totalRAMUsed']
    limits['cpu'] = lim['maxTotalCores'] - lim['totalCoresUsed']
    limits['instances'] = lim['maxTotalInstances'] - lim['totalInstancesUsed']
    if CONF.use_neutron:
        return limits
    if CONF.use_floating_ips:
        limits['floatingips'] = (
            lim['maxTotalFloatingIps'] - lim['totalFloatingIpsUsed'])
    limits['security_groups'] = (
        lim['maxSecurityGroups'] - lim['totalSecurityGroupsUsed'])
    limits['security_group_rules'] = lim['maxSecurityGroupRules']
    return limits


def _get_neutron_limits():
    limits = {}
    if not CONF.use_neutron:
        return limits
    neutron = neutron_client.client()
    tenant_id = context.ctx().tenant_id
    total_lim = neutron.show_quota(tenant_id)['quota']
    if CONF.use_floating_ips:
        usage_fip = neutron.list_floatingips(
            tenant_id=tenant_id)['floatingips']
        limits['floatingips'] = total_lim['floatingip'] - len(usage_fip)
    usage_sg = (
        neutron.list_security_groups(tenant_id=tenant_id)['security_groups'])
    limits['security_groups'] = total_lim['security_group'] - len(usage_sg)

    usage_sg_rules = (neutron.list_security_group_rules(
        tenant_id=tenant_id)['security_group_rules'])
    limits['security_group_rules'] = (
        total_lim['security_group_rule'] - len(usage_sg_rules))
    usage_ports = neutron.list_ports(tenant_id=tenant_id)['ports']
    limits['ports'] = total_lim['port'] - len(usage_ports)
    return limits


def _get_cinder_limits():
    avail_limits = {}
    cinder = cinder_client.client()
    lim = {}
    for l in cinder.limits.get().absolute:
        lim[l.name] = l.value
    avail_limits['volumes'] = lim['maxTotalVolumes'] - lim['totalVolumesUsed']
    avail_limits['volume_gbs'] = (
        lim['maxTotalVolumeGigabytes'] - lim['totalGigabytesUsed'])
    return avail_limits
