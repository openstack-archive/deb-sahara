# Copyright (c) 2014 OpenStack Foundation
# Copyright (c) 2015 ISPRAS
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

from sahara.plugins.spark import edp_engine as spark_edp
from sahara.tests.unit.service.edp.spark import base as tests


class TestSparkPlugin(tests.TestSpark):
    def setUp(self):
        super(TestSparkPlugin, self).setUp()
        self.master_host = "master"
        self.engine_class = spark_edp.EdpEngine
        self.spark_user = ""
        self.spark_submit = (
            "%(spark_home)s/bin/spark-submit" %
            {"spark_home": self.spark_home})
        self.master = (
            "spark://%(master_host)s:%(master_port)s" %
            {"master_host": self.master_host,
             "master_port": self.master_port})
        self.deploy_mode = "client"
