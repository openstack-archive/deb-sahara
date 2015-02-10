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

from sahara import context
from sahara.service.edp.binary_retrievers import internal_swift as i_swift
from sahara.service.edp.binary_retrievers import sahara_db as db
from sahara.swift import utils as su


def get_raw_binary(job_binary, proxy_configs=None, with_context=False):
    '''Get the raw data for a job binary

    This will retrieve the raw data for a job binary from it's source. In the
    case of Swift based binaries there is a precedence of credentials for
    authenticating the client. Requesting a context based authentication takes
    precendence over proxy user which takes precendence over embedded
    credentials.

    :param job_binary: The job binary to retrieve
    :param proxy_configs: Proxy user configuration to use as credentials
    :param with_context: Use the current context as credentials
    :returns: The raw data from a job binary

    '''
    url = job_binary.url
    if url.startswith("internal-db://"):
        res = db.get_raw_data(context.ctx(), job_binary)

    if url.startswith(su.SWIFT_INTERNAL_PREFIX):
        if with_context:
            res = i_swift.get_raw_data_with_context(job_binary)
        else:
            res = i_swift.get_raw_data(job_binary, proxy_configs)

    return res
