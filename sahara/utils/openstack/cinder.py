# -*- coding: utf-8 -*-
# Copyright (c) 2013 Mirantis Inc.
# Copyright (c) 2014 Adrien Vergé <adrien.verge@numergy.com>
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

from cinderclient.v1 import client as cinder_client_v1
from cinderclient.v2 import client as cinder_client_v2
from oslo.config import cfg

from sahara import context
from sahara.i18n import _
from sahara.openstack.common import log as logging
from sahara.utils.openstack import base


LOG = logging.getLogger(__name__)


opts = [
    cfg.IntOpt('cinder_api_version', default=2,
               help='Version of the Cinder API to use.')
]

CONF = cfg.CONF
CONF.register_opts(opts)


def validate_config():
    if CONF.cinder_api_version == 1:
        LOG.warn(_('The Cinder v1 API is deprecated and will be removed after '
                   'the Juno release.  You should set cinder_api_version=2 in '
                   'your sahara.conf file.'))
    elif CONF.cinder_api_version != 2:
        LOG.warn(_('Unsupported Cinder API version: %(bad)s.  Please set a '
                   'correct value for cinder_api_version in your sahara.conf '
                   'file (currently supported versions are: %(supported)s).  '
                   'Falling back to Cinder API version 2.'),
                 {'bad': CONF.cinder_api_version, 'supported': [1, 2]})
        CONF.set_override('cinder_api_version', 2)


def client():
    ctx = context.current()
    if CONF.cinder_api_version == 1:
        volume_url = base.url_for(ctx.service_catalog, 'volume')
        cinder = cinder_client_v1.Client(ctx.username, ctx.auth_token,
                                         ctx.tenant_id, volume_url)
    else:
        volume_url = base.url_for(ctx.service_catalog, 'volumev2')
        cinder = cinder_client_v2.Client(ctx.username, ctx.auth_token,
                                         ctx.tenant_id, volume_url)

    cinder.client.auth_token = ctx.auth_token
    cinder.client.management_url = volume_url

    return cinder


def get_volumes():
    return [volume.id for volume in client().volumes.list()]


def get_volume(volume_id):
    return client().volumes.get(volume_id)
