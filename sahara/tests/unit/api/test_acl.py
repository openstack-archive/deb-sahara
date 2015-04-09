# Copyright (c) 2014 Mirantis Inc.
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

from oslo_policy import policy as cpolicy

from sahara.api import acl
from sahara import exceptions as ex
from sahara.tests.unit import base


class TestAcl(base.SaharaTestCase):

    def _set_policy(self, json):
        acl.setup_policy()
        rules = cpolicy.Rules.load_json(json)
        acl.ENFORCER.set_rules(rules, use_conf=False)

    def test_policy_allow(self):
        @acl.enforce("clusters:get_all")
        def test():
            pass

        json = '{"clusters:get_all": ""}'
        self._set_policy(json)

        test()

    def test_policy_deny(self):
        @acl.enforce("clusters:get_all")
        def test():
            pass

        json = '{"clusters:get_all": "!"}'
        self._set_policy(json)

        self.assertRaises(ex.Forbidden, test)
