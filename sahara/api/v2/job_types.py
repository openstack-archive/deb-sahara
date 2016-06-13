# Copyright (c) 2016 Red Hat, Inc.
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

from sahara.api import acl
from sahara.service.api.v2 import job_types as api
import sahara.utils.api as u


rest = u.RestV2('job-types', __name__)


@rest.get('/job-types')
@acl.enforce("data-processing:job-types:get_all")
def job_types_get():
    # We want to use flat=False with to_dict() so that
    # the value of each arg is given as a list. This supports
    # filters of the form ?type=Pig&type=Java, etc.
    return u.render(job_types=api.get_job_types(
        **u.get_request_args().to_dict(flat=False)))
