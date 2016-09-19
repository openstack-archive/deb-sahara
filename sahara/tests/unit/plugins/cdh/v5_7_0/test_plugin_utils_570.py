# Copyright (c) 2015 Intel Corporation.
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

from sahara.plugins.cdh.v5_7_0 import plugin_utils as pu
from sahara.tests.unit.plugins.cdh import base_plugin_utils_test


class TestPluginUtilsV570(base_plugin_utils_test.TestPluginUtilsHigherThanV5):

    def setUp(self):
        super(TestPluginUtilsV570, self).setUp()
        self.plug_utils = pu.PluginUtilsV570()
        self.version = "v5_7_0"
