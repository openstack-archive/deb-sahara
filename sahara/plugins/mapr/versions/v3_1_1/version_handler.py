# Copyright (c) 2015, MapR Technologies
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


from sahara.plugins.mapr.base import base_version_handler as bvh
from sahara.plugins.mapr.services.drill import drill
from sahara.plugins.mapr.services.flume import flume
from sahara.plugins.mapr.services.hbase import hbase
from sahara.plugins.mapr.services.hive import hive
from sahara.plugins.mapr.services.httpfs import httpfs
from sahara.plugins.mapr.services.hue import hue
from sahara.plugins.mapr.services.impala import impala
from sahara.plugins.mapr.services.mahout import mahout
from sahara.plugins.mapr.services.management import management
from sahara.plugins.mapr.services.mapreduce import mapreduce
from sahara.plugins.mapr.services.maprfs import maprfs
from sahara.plugins.mapr.services.oozie import oozie
from sahara.plugins.mapr.services.pig import pig
from sahara.plugins.mapr.services.sqoop import sqoop2
from sahara.plugins.mapr.services.swift import swift
import sahara.plugins.mapr.versions.v3_1_1.context as c
import sahara.plugins.mapr.versions.v3_1_1.edp_engine as edp


version = '3.1.1'


class VersionHandler(bvh.BaseVersionHandler):
    def __init__(self):
        super(VersionHandler, self).__init__()
        self._version = version
        self._required_services = [
            mapreduce.MapReduce(),
            maprfs.MapRFS(),
            management.Management(),
            oozie.Oozie(),
        ]
        self._services = [
            mapreduce.MapReduce(),
            maprfs.MapRFS(),
            management.Management(),
            oozie.Oozie(),
            hive.HiveV012(),
            hive.HiveV013(),
            hbase.HBaseV094(),
            hbase.HBaseV098(),
            httpfs.HttpFS(),
            mahout.Mahout(),
            pig.Pig(),
            swift.Swift(),
            flume.Flume(),
            drill.Drill(),
            sqoop2.Sqoop2(),
            impala.ImpalaV123(),
            hue.Hue(),
        ]

    def get_context(self, cluster, added=None, removed=None):
        return c.Context(cluster, self, added, removed)

    def get_edp_engine(self, cluster, job_type):
        if job_type in edp.MapR3OozieJobEngine.get_supported_job_types():
            return edp.MapR3OozieJobEngine(cluster)
        return None

    def get_edp_job_types(self):
        return edp.MapR3OozieJobEngine.get_supported_job_types()

    def get_edp_config_hints(self, job_type):
        return edp.MapR3OozieJobEngine.get_possible_job_config(job_type)
