# Copyright (c) 2016 Red Hat Inc.
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

from oslo_config import cfg

CONF = cfg.CONF


def has_floating_ip(instance):

    # Alternatively in each of these cases
    # we could use the nova client to look up the
    # ips for the instance and check the attributes
    # to ensure that the management_ip is a floating
    # ip, but a simple comparison with the internal_ip
    # corresponds with the logic in
    # sahara.service.networks.init_instances_ips
    if CONF.use_neutron and not instance.node_group.floating_ip_pool:
        return False

    # in the neutron case comparing ips is an extra simple check ...
    # maybe allocation of a floating ip failed for some reason

    # (Alternatively in each of these cases
    # we could use the nova client to look up the
    # ips for the instance and check the attributes
    # to ensure that the management_ip is a floating
    # ip, but a simple comparison with the internal_ip
    # corresponds with the logic in
    # sahara.service.networks.init_instances_ips)
    return instance.management_ip != instance.internal_ip
