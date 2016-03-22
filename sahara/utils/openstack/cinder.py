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

from cinderclient.v2 import client as cinder_client_v2
from oslo_config import cfg
from oslo_log import log as logging

from sahara import context
from sahara import exceptions as ex
from sahara.i18n import _LW
from sahara.service import sessions
from sahara.utils.openstack import base
from sahara.utils.openstack import keystone


LOG = logging.getLogger(__name__)


opts = [
    cfg.IntOpt('api_version', default=2,
               help='Version of the Cinder API to use.',
               deprecated_name='cinder_api_version'),
    cfg.BoolOpt('api_insecure',
                default=False,
                help='Allow to perform insecure SSL requests to cinder.'),
    cfg.StrOpt('ca_file',
               help='Location of ca certificates file to use for cinder '
                    'client requests.'),
    cfg.StrOpt("endpoint_type",
               default="internalURL",
               help="Endpoint type for cinder client requests")
]

cinder_group = cfg.OptGroup(name='cinder',
                            title='Cinder client options')

CONF = cfg.CONF
CONF.register_group(cinder_group)
CONF.register_opts(opts, group=cinder_group)


def validate_config():
    if CONF.cinder.api_version != 2:
        LOG.warning(_LW('Unsupported Cinder API version: {bad}.  Please set a '
                        'correct value for cinder.api_version in your '
                        'sahara.conf file (currently supported versions are: '
                        '{supported}). Falling back to Cinder API version 2.')
                    .format(bad=CONF.cinder.api_version,
                            supported=[2]))
        CONF.set_override('api_version', 2, group='cinder', enforce_type=True)


def client():
    session = sessions.cache().get_session(sessions.SESSION_TYPE_CINDER)
    cinder = cinder_client_v2.Client(
        session=session, auth=keystone.auth(),
        endpoint_type=CONF.cinder.endpoint_type,
        region_name=CONF.os_region_name)
    return cinder


def check_cinder_exists():
    service_type = 'volumev2'
    try:
        base.url_for(context.current().service_catalog, service_type,
                     endpoint_type=CONF.cinder.endpoint_type)
        return True
    except ex.SystemError:
        return False


def get_volume(volume_id):
    return base.execute_with_retries(client().volumes.get, volume_id)
