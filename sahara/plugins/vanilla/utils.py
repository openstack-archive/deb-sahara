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

from sahara.plugins import utils as u


def get_namenode(cluster):
    return u.get_instance(cluster, "namenode")


def get_jobtracker(cluster):
    instance = u.get_instance(cluster, "jobtracker")

    return instance


def get_resourcemanager(cluster):
    return u.get_instance(cluster, 'resourcemanager')


def get_nodemanagers(cluster):
    return u.get_instances(cluster, 'nodemanager')


def get_oozie(cluster):
    return u.get_instance(cluster, "oozie")


def get_hiveserver(cluster):
    return u.get_instance(cluster, "hiveserver")


def get_datanodes(cluster):
    return u.get_instances(cluster, 'datanode')


def get_tasktrackers(cluster):
    return u.get_instances(cluster, 'tasktracker')


def get_secondarynamenodes(cluster):
    return u.get_instances(cluster, 'secondarynamenode')


def get_historyserver(cluster):
    return u.get_instance(cluster, 'historyserver')


def get_instance_hostname(instance):
    return instance.hostname() if instance else None
