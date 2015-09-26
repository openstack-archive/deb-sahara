# Copyright (c) 2015 Mirantis Inc.
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


import functools
import telnetlib

from oslo_log import log as logging
from oslo_utils import uuidutils

from sahara import conductor
from sahara import context
from sahara.i18n import _
from sahara.plugins.ambari import client as ambari_client
from sahara.plugins.ambari import common as p_common
from sahara.plugins.ambari import configs
from sahara.plugins import exceptions as p_exc
from sahara.plugins import utils as plugin_utils
from sahara.utils import poll_utils


LOG = logging.getLogger(__name__)
conductor = conductor.API


repo_id_map = {
    "2.2": {
        "HDP": "HDP-2.2",
        "HDP-UTILS": "HDP-UTILS-1.1.0.20"
    },
    "2.3": {
        "HDP": "HDP-2.3",
        "HDP-UTILS": "HDP-UTILS-1.1.0.20"
    }
}

os_type_map = {
    "centos6": "redhat6",
    "redhat6": "redhat6"
}


def setup_ambari(cluster):
    LOG.debug("Set up Ambari management console")
    ambari = plugin_utils.get_instance(cluster, p_common.AMBARI_SERVER)
    with ambari.remote() as r:
        sudo = functools.partial(r.execute_command, run_as_root=True)
        sudo("ambari-server setup -s -j"
             " `cut -f2 -d \"=\" /etc/profile.d/99-java.sh`", timeout=1800)
        sudo("service ambari-server start")
    LOG.debug("Ambari management console installed")


def setup_agents(cluster):
    LOG.debug("Set up Ambari agents")
    manager_address = plugin_utils.get_instance(
        cluster, p_common.AMBARI_SERVER).fqdn()
    with context.ThreadGroup() as tg:
        for inst in plugin_utils.get_instances(cluster):
            tg.spawn("hwx-agent-setup-%s" % inst.id,
                     _setup_agent, inst, manager_address)
    LOG.debug("Ambari agents has been installed")


def _setup_agent(instance, ambari_address):
    with instance.remote() as r:
        sudo = functools.partial(r.execute_command, run_as_root=True)
        r.replace_remote_string("/etc/ambari-agent/conf/ambari-agent.ini",
                                "localhost", ambari_address)
        sudo("service ambari-agent start")
        # for correct installing packages
        sudo("yum clean all")


def wait_ambari_accessible(cluster):
    ambari = plugin_utils.get_instance(cluster, p_common.AMBARI_SERVER)
    kwargs = {"host": ambari.management_ip, "port": 8080}
    poll_utils.poll(_check_port_accessible, kwargs=kwargs, timeout=300)


def _check_port_accessible(host, port):
    try:
        conn = telnetlib.Telnet(host, port)
        conn.close()
        return True
    except IOError:
        return False


def _prepare_ranger(cluster):
    ranger = plugin_utils.get_instance(cluster, p_common.RANGER_ADMIN)
    if not ranger:
        return
    ambari = plugin_utils.get_instance(cluster, p_common.AMBARI_SERVER)
    with ambari.remote() as r:
        r.execute_command("sudo yum install -y mysql-connector-java")
        r.execute_command(
            "sudo ambari-server setup --jdbc-db=mysql "
            "--jdbc-driver=/usr/share/java/mysql-connector-java.jar")
    init_db_template = """
create user 'root'@'%' identified by '{password}';
set password for 'root'@'localhost' = password('{password}');"""
    password = uuidutils.generate_uuid()
    extra = cluster.extra.to_dict() if cluster.extra else {}
    extra["ranger_db_password"] = password
    ctx = context.ctx()
    conductor.cluster_update(ctx, cluster, {"extra": extra})
    with ranger.remote() as r:
        sudo = functools.partial(r.execute_command, run_as_root=True)
        # TODO(sreshetnyak): add ubuntu support
        sudo("yum install -y mysql-server")
        sudo("service mysqld start")
        r.write_file_to("/tmp/init.sql",
                        init_db_template.format(password=password))
        sudo("mysql < /tmp/init.sql")
        sudo("rm /tmp/init.sql")


def update_default_ambari_password(cluster):
    ambari = plugin_utils.get_instance(cluster, p_common.AMBARI_SERVER)
    new_password = uuidutils.generate_uuid()
    with ambari_client.AmbariClient(ambari) as client:
        client.update_user_password("admin", "admin", new_password)
    extra = cluster.extra.to_dict() if cluster.extra else {}
    extra["ambari_password"] = new_password
    ctx = context.ctx()
    conductor.cluster_update(ctx, cluster, {"extra": extra})
    cluster = conductor.cluster_get(ctx, cluster.id)


def wait_host_registration(cluster):
    ambari = plugin_utils.get_instance(cluster, p_common.AMBARI_SERVER)
    hosts = plugin_utils.get_instances(cluster)
    password = cluster.extra["ambari_password"]
    with ambari_client.AmbariClient(ambari, password=password) as client:
        kwargs = {"client": client, "num_hosts": len(hosts)}
        poll_utils.poll(_check_host_registration, kwargs=kwargs, timeout=600)
        registered_hosts = client.get_registered_hosts()
    registered_host_names = [h["Hosts"]["host_name"] for h in registered_hosts]
    actual_host_names = [h.fqdn() for h in hosts]
    if sorted(registered_host_names) != sorted(actual_host_names):
        raise p_exc.HadoopProvisionError(
            _("Host registration fails in Ambari"))


def _check_host_registration(client, num_hosts):
    hosts = client.get_registered_hosts()
    return len(hosts) == num_hosts


def set_up_hdp_repos(cluster):
    hdp_repo = configs.get_hdp_repo_url(cluster)
    hdp_utils_repo = configs.get_hdp_utils_repo_url(cluster)
    if not hdp_repo and not hdp_utils_repo:
        return
    ambari = plugin_utils.get_instance(cluster, p_common.AMBARI_SERVER)
    password = cluster.extra["ambari_password"]
    pv = cluster.hadoop_version
    repos = repo_id_map[pv]
    with ambari_client.AmbariClient(ambari, password=password) as client:
        os_type = os_type_map[client.get_host_info(ambari.fqdn())["os_type"]]
        if hdp_repo:
            client.set_up_mirror(pv, os_type, repos["HDP"], hdp_repo)
        if hdp_utils_repo:
            client.set_up_mirror(pv, os_type, repos["HDP-UTILS"],
                                 hdp_utils_repo)


def create_blueprint(cluster):
    _prepare_ranger(cluster)
    cluster = conductor.cluster_get(context.ctx(), cluster.id)
    host_groups = []
    for ng in cluster.node_groups:
        procs = p_common.get_ambari_proc_list(ng)
        procs.extend(p_common.get_clients(cluster))
        for instance in ng.instances:
            hg = {
                "name": instance.instance_name,
                "configurations": configs.get_instance_params(instance),
                "components": []
            }
            for proc in procs:
                hg["components"].append({"name": proc})
            host_groups.append(hg)
    bp = {
        "Blueprints": {
            "stack_name": "HDP",
            "stack_version": cluster.hadoop_version
        },
        "host_groups": host_groups,
        "configurations": configs.get_cluster_params(cluster)
    }
    ambari = plugin_utils.get_instance(cluster, p_common.AMBARI_SERVER)
    password = cluster.extra["ambari_password"]
    with ambari_client.AmbariClient(ambari, password=password) as client:
        client.create_blueprint(cluster.name, bp)


def start_cluster(cluster):
    cl_tmpl = {
        "blueprint": cluster.name,
        "default_password": uuidutils.generate_uuid(),
        "host_groups": []
    }
    for ng in cluster.node_groups:
        for instance in ng.instances:
            cl_tmpl["host_groups"].append({
                "name": instance.instance_name,
                "hosts": [{"fqdn": instance.fqdn()}]
            })
    ambari = plugin_utils.get_instance(cluster, p_common.AMBARI_SERVER)
    password = cluster.extra["ambari_password"]
    with ambari_client.AmbariClient(ambari, password=password) as client:
        req_id = client.create_cluster(cluster.name, cl_tmpl)["id"]
        while True:
            status = client.check_request_status(cluster.name, req_id)
            LOG.debug("Task %s in %s state. Completed %.1f%%" % (
                status["request_context"], status["request_status"],
                status["progress_percent"]))
            if status["request_status"] == "COMPLETED":
                return
            if status["request_status"] in ["IN_PROGRESS", "PENDING"]:
                context.sleep(5)
            else:
                raise p_exc.HadoopProvisionError(
                    _("Ambari request in %s state") % status["request_status"])
