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

import sahara.exceptions as e
from sahara.i18n import _
from sahara.utils import api_validator as a


def check_job_binary_internal(data, **kwargs):
    if not (type(data) is str and len(data) > 0):
        raise e.BadJobBinaryInternalException()
    if "name" in kwargs:
        name = kwargs["name"]
        if not a.validate_name_format(name):
            raise e.BadJobBinaryInternalException(_("%s is not a valid name")
                                                  % name)
