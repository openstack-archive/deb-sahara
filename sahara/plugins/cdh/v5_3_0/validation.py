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

from sahara.i18n import _
from sahara.plugins.cdh.v5_3_0 import plugin_utils as pu
from sahara.plugins import exceptions as ex
from sahara.plugins import utils as u
from sahara.utils import general as gu

PU = pu.PluginUtilsV530()


def validate_cluster_creating(cluster):
    mng_count = _get_inst_count(cluster, 'CLOUDERA_MANAGER')
    if mng_count != 1:
        raise ex.InvalidComponentCountException('CLOUDERA_MANAGER',
                                                1, mng_count)

    nn_count = _get_inst_count(cluster, 'HDFS_NAMENODE')
    if nn_count != 1:
        raise ex.InvalidComponentCountException('HDFS_NAMENODE', 1, nn_count)

    snn_count = _get_inst_count(cluster, 'HDFS_SECONDARYNAMENODE')
    if snn_count != 1:
        raise ex.InvalidComponentCountException('HDFS_SECONDARYNAMENODE', 1,
                                                snn_count)

    rm_count = _get_inst_count(cluster, 'YARN_RESOURCEMANAGER')
    if rm_count not in [0, 1]:
        raise ex.InvalidComponentCountException('YARN_RESOURCEMANAGER',
                                                _('0 or 1'), rm_count)

    hs_count = _get_inst_count(cluster, 'YARN_JOBHISTORY')
    if hs_count not in [0, 1]:
        raise ex.InvalidComponentCountException('YARN_JOBHISTORY',
                                                _('0 or 1'), hs_count)

    if rm_count > 0 and hs_count < 1:
        raise ex.RequiredServiceMissingException(
            'YARN_JOBHISTORY', required_by='YARN_RESOURCEMANAGER')

    nm_count = _get_inst_count(cluster, 'YARN_NODEMANAGER')
    if rm_count == 0:
        if nm_count > 0:
            raise ex.RequiredServiceMissingException(
                'YARN_RESOURCEMANAGER', required_by='YARN_NODEMANAGER')

    oo_count = _get_inst_count(cluster, 'OOZIE_SERVER')
    dn_count = _get_inst_count(cluster, 'HDFS_DATANODE')
    if oo_count not in [0, 1]:
        raise ex.InvalidComponentCountException('OOZIE_SERVER', _('0 or 1'),
                                                oo_count)

    if oo_count == 1:
        if dn_count < 1:
            raise ex.RequiredServiceMissingException(
                'HDFS_DATANODE', required_by='OOZIE_SERVER')

        if nm_count < 1:
            raise ex.RequiredServiceMissingException(
                'YARN_NODEMANAGER', required_by='OOZIE_SERVER')

        if hs_count != 1:
            raise ex.RequiredServiceMissingException(
                'YARN_JOBHISTORY', required_by='OOZIE_SERVER')

    hms_count = _get_inst_count(cluster, 'HIVE_METASTORE')
    hvs_count = _get_inst_count(cluster, 'HIVE_SERVER2')
    whc_count = _get_inst_count(cluster, 'HIVE_WEBHCAT')

    if hms_count and rm_count < 1:
        raise ex.RequiredServiceMissingException(
            'YARN_RESOURCEMANAGER', required_by='HIVE_METASTORE')

    if hms_count and not hvs_count:
        raise ex.RequiredServiceMissingException(
            'HIVE_SERVER2', required_by='HIVE_METASTORE')

    if hvs_count and not hms_count:
        raise ex.RequiredServiceMissingException(
            'HIVE_METASTORE', required_by='HIVE_SERVER2')

    if whc_count and not hms_count:
        raise ex.RequiredServiceMissingException(
            'HIVE_METASTORE', required_by='HIVE_WEBHCAT')

    hue_count = _get_inst_count(cluster, 'HUE_SERVER')
    if hue_count not in [0, 1]:
        raise ex.InvalidComponentCountException('HUE_SERVER', _('0 or 1'),
                                                hue_count)

    shs_count = _get_inst_count(cluster, 'SPARK_YARN_HISTORY_SERVER')
    if shs_count not in [0, 1]:
        raise ex.InvalidComponentCountException('SPARK_YARN_HISTORY_SERVER',
                                                _('0 or 1'), shs_count)
    if shs_count and not rm_count:
        raise ex.RequiredServiceMissingException(
            'YARN_RESOURCEMANAGER', required_by='SPARK_YARN_HISTORY_SERVER')

    if oo_count < 1 and hue_count:
        raise ex.RequiredServiceMissingException(
            'OOZIE_SERVER', required_by='HUE_SERVER')

    if hms_count < 1 and hue_count:
        raise ex.RequiredServiceMissingException(
            'HIVE_METASTORE', required_by='HUE_SERVER')

    hbm_count = _get_inst_count(cluster, 'HBASE_MASTER')
    hbr_count = _get_inst_count(cluster, 'HBASE_REGIONSERVER')
    zk_count = _get_inst_count(cluster, 'ZOOKEEPER_SERVER')

    if hbm_count >= 1:
        if zk_count < 1:
            raise ex.RequiredServiceMissingException('ZOOKEEPER',
                                                     required_by='HBASE')
        if hbr_count < 1:
            raise ex.InvalidComponentCountException(
                'HBASE_REGIONSERVER', _('at least 1'), hbr_count)
    elif hbr_count >= 1:
        raise ex.InvalidComponentCountException('HBASE_MASTER',
                                                _('at least 1'), hbm_count)

    a_count = _get_inst_count(cluster, 'FLUME_AGENT')
    if a_count >= 1:
        if dn_count < 1:
            raise ex.RequiredServiceMissingException(
                'HDFS_DATANODE', required_by='FLUME_AGENT')

    snt_count = _get_inst_count(cluster, 'SENTRY_SERVER')
    if snt_count not in [0, 1]:
        raise ex.InvalidComponentCountException('SENTRY_SERVER', _('0 or 1'),
                                                snt_count)
    if snt_count == 1:
        if dn_count < 1:
            raise ex.RequiredServiceMissingException(
                'HDFS_DATANODE', required_by='SENTRY_SERVER')
        if zk_count < 1:
            raise ex.RequiredServiceMissingException(
                'ZOOKEEPER', required_by='SENTRY_SERVER')

    slr_count = _get_inst_count(cluster, 'SOLR_SERVER')
    if slr_count >= 1:
        if dn_count < 1:
            raise ex.RequiredServiceMissingException(
                'HDFS_DATANODE', required_by='SOLR_SERVER')
        if zk_count < 1:
            raise ex.RequiredServiceMissingException(
                'ZOOKEEPER', required_by='SOLR_SERVER')

    s2s_count = _get_inst_count(cluster, 'SQOOP_SERVER')
    if s2s_count not in [0, 1]:
        raise ex.InvalidComponentCountException('SQOOP_SERVER', _('0 or 1'),
                                                s2s_count)
    if s2s_count == 1:
        if dn_count < 1:
            raise ex.RequiredServiceMissingException(
                'HDFS_DATANODE', required_by='SQOOP_SERVER')
        if nm_count < 1:
            raise ex.RequiredServiceMissingException(
                'YARN_NODEMANAGER', required_by='SQOOP_SERVER')
        if hs_count != 1:
            raise ex.RequiredServiceMissingException(
                'YARN_JOBHISTORY', required_by='SQOOP_SERVER')

    lhbi_count = _get_inst_count(cluster, 'HBASE_INDEXER')
    if lhbi_count >= 1:
        if dn_count < 1:
            raise ex.RequiredServiceMissingException(
                'HDFS_DATANODE', required_by='HBASE_INDEXER')
        if zk_count < 1:
            raise ex.RequiredServiceMissingException(
                'ZOOKEEPER', required_by='HBASE_INDEXER')
        if slr_count < 1:
            raise ex.RequiredServiceMissingException(
                'SOLR_SERVER', required_by='HBASE_INDEXER')
        if hbm_count < 1:
            raise ex.RequiredServiceMissingException(
                'HBASE_MASTER', required_by='HBASE_INDEXER')

    ics_count = _get_inst_count(cluster, 'IMPALA_CATALOGSERVER')
    iss_count = _get_inst_count(cluster, 'IMPALA_STATESTORE')
    id_count = _get_inst_count(cluster, 'IMPALAD')
    if ics_count not in [0, 1]:
        raise ex.InvalidComponentCountException('IMPALA_CATALOGSERVER',
                                                _('0 or 1'), ics_count)
    if iss_count not in [0, 1]:
        raise ex.InvalidComponentCountException('IMPALA_STATESTORE',
                                                _('0 or 1'), iss_count)
    if ics_count == 1:
        if iss_count != 1:
            raise ex.RequiredServiceMissingException(
                'IMPALA_STATESTORE', required_by='IMPALA')
        if id_count < 1:
            raise ex.RequiredServiceMissingException(
                'IMPALAD', required_by='IMPALA')
        if dn_count < 1:
            raise ex.RequiredServiceMissingException(
                'HDFS_DATANODE', required_by='IMPALA')
        if hms_count < 1:
            raise ex.RequiredServiceMissingException(
                'HIVE_METASTORE', required_by='IMPALA')


def validate_additional_ng_scaling(cluster, additional):
    rm = PU.get_resourcemanager(cluster)
    scalable_processes = _get_scalable_processes()

    for ng_id in additional:
        ng = gu.get_by_id(cluster.node_groups, ng_id)
        if not set(ng.node_processes).issubset(scalable_processes):
            msg = _("CDH plugin cannot scale nodegroup with processes: "
                    "%(processes)s")
            raise ex.NodeGroupCannotBeScaled(
                ng.name, msg % {'processes': ' '.join(ng.node_processes)})

        if not rm and 'YARN_NODEMANAGER' in ng.node_processes:
            msg = _("CDH plugin cannot scale node group with processes "
                    "which have no master-processes run in cluster")
            raise ex.NodeGroupCannotBeScaled(ng.name, msg)


def validate_existing_ng_scaling(cluster, existing):
    scalable_processes = _get_scalable_processes()
    dn_to_delete = 0
    for ng in cluster.node_groups:
        if ng.id in existing:
            if ng.count > existing[ng.id] and "datanode" in ng.node_processes:
                dn_to_delete += ng.count - existing[ng.id]

            if not set(ng.node_processes).issubset(scalable_processes):
                msg = _("CDH plugin cannot scale nodegroup with processes: "
                        "%(processes)s")
                raise ex.NodeGroupCannotBeScaled(
                    ng.name, msg % {'processes': ' '.join(ng.node_processes)})


def _get_scalable_processes():
    return ['HDFS_DATANODE', 'YARN_NODEMANAGER']


def _get_inst_count(cluster, process):
    return sum([ng.count for ng in u.get_node_groups(cluster, process)])
