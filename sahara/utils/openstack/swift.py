# Copyright (c) 2014 Red Hat, Inc.
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
import swiftclient

from sahara.swift import swift_helper as sh
from sahara.swift import utils as su
from sahara.utils.openstack import base
from sahara.utils.openstack import keystone as k

opts = [
    cfg.BoolOpt('api_insecure',
                default=False,
                help='Allow to perform insecure SSL requests to swift.'),
    cfg.StrOpt('ca_file',
               help='Location of ca certificates file to use for swift '
                    'client requests.'),
    cfg.StrOpt("endpoint_type",
               default="internalURL",
               help="Endpoint type for swift client requests")
]

swift_group = cfg.OptGroup(name='swift',
                           title='Swift client options')

CONF = cfg.CONF
CONF.register_group(swift_group)
CONF.register_opts(opts, group=swift_group)


def client(username, password, trust_id=None):
    '''return a Swift client

    This will return a Swift client for the specified username scoped to the
    current context project, unless a trust identifier is specified.

    If a trust identifier is present then the Swift client will be created
    based on a preauthorized token generated by the username scoped to the
    trust identifier.

    :param username: The username for the Swift client
    :param password: The password associated with the username
    :param trust_id: A trust identifier for scoping the username (optional)
    :returns: A Swift client object

    '''
    if trust_id:
        proxyauth = k.auth_for_proxy(username, password, trust_id)
        return client_from_token(k.token_from_auth(proxyauth))
    else:
        return swiftclient.Connection(
            auth_version='2.0',
            cacert=CONF.swift.ca_file,
            insecure=CONF.swift.api_insecure,
            authurl=su.retrieve_auth_url(),
            user=username,
            key=password,
            tenant_name=sh.retrieve_tenant(),
            retries=CONF.retries.retries_number,
            retry_on_ratelimit=True,
            starting_backoff=CONF.retries.retry_after,
            max_backoff=CONF.retries.retry_after)


def client_from_token(token):
    '''return a Swift client authenticated from a token.'''
    return swiftclient.Connection(auth_version='2.0',
                                  cacert=CONF.swift.ca_file,
                                  insecure=CONF.swift.api_insecure,
                                  preauthurl=base.url_for(
                                      service_type="object-store",
                                      endpoint_type=CONF.swift.endpoint_type),
                                  preauthtoken=token,
                                  retries=CONF.retries.retries_number,
                                  retry_on_ratelimit=True,
                                  starting_backoff=CONF.retries.retry_after,
                                  max_backoff=CONF.retries.retry_after)
