Cloudera Plugin
===============

The Cloudera plugin is a Sahara plugin which allows the user to
deploy and operate a cluster with Cloudera Manager.

The Cloudera plugin is enabled in Sahara by default. You can manually
modify the Sahara configuration file (default /etc/sahara/sahara.conf) to
explicitly enable or disable it in "plugins" line.

You need to build images using :doc:`cdh_imagebuilder` to produce images used
to provision cluster. They already have Cloudera Express installed (5.0.0 or
5.3.0 version).

The cloudera plugin requires an image to be tagged in Sahara Image Registry with
two tags: 'cdh' and '<cloudera version>' (e.g. '5' or '5.3.0').

The default username specified for these images is different for each
distribution:

+--------------+------------+
| OS           | username   |
+==============+============+
| Ubuntu 12.04 | ubuntu     |
+--------------+------------+
| CentOS 6.5   | cloud-user |
+--------------+------------+

Services Supported
------------------

Currently below services are supported in both versions of Cloudera plugin:
HDFS, Oozie, YARN, Spark, Zookeeper, Hive, Hue, HBase. 5.3.0 version
of Cloudera Plugin also supported following services: Impala, Flume, Solr, Sqoop,
and Key-value Store Indexer.

.. note::

    Sentry service is enabled in Cloudera plugin. However, for we do not enable
    Kerberos authentication in the cluster, which is required for Sentry
    functionality, using Sentry service will not really take any effect, and
    other services depending on Sentry will not do any authentication too.


Cluster Validation
------------------

When the user performs an operation on the cluster using a Cloudera plugin, the
cluster topology requested by the user is verified for consistency.

The following limitations are required in the cluster topology for the both
cloudera plugin versions:

  + Cluster must contain exactly one manager.
  + Cluster must contain exactly one namenode.
  + Cluster must contain exactly one secondarynamenode.
  + Cluster can contain at most one resourcemanager and this process is also
    required by nodemanager.
  + Cluster can contain at most one jobhistory and this process is also
    requried for resourcemanager.
  + Cluster can contain at most one oozie and this process is also required
    for EDP.
  + Cluster can't contain oozie without datanode.
  + Cluster can't contain oozie without nodemanager.
  + Cluster can't contain oozie without jobhistory.
  + Cluster can't contain hive on the cluster without the following services:
    metastore, hive server, webcat and resourcemanager.
  + Cluster can contain at most one hue server.
  + Cluster can't contain hue server without hive service and oozie.
  + Cluster can contain at most one spark history server.
  + Cluster can't contain spark history server without resourcemanager.
  + Cluster can't contain hbase master service without at least one zookeeper
    and at least one hbase regionserver.
  + Cluster can't contain hbase regionserver without at least one hbase maser.

In case of 5.3.0 version of Cloudera Plugin there are few extra limitations
in the cluster topology:

  + Cluster can't contain flume without at least one datanode.
  + Cluster can contain at most one sentry server service.
  + Cluster can't contain sentry server service without at least one zookeeper
    and at least one datanode.
  + Cluster can't contain solr server without at least one zookeeper and at
    least one datanode.
  + Cluster can contain at most one sqoop server.
  + Cluster can't contain sqoop server without at least one datanode,
    nodemanager and jobhistory.
  + Cluster can't contain hbase indexer without at least one datanode,
    zookeeper, solr server and hbase master.
  + Cluster can contain at most one impala catalog server.
  + Cluster can contain at most one impala statestore.
  + Cluster can't contain impala catalogserver without impala statestore,
    at least one impalad service, at least one datanode, and metastore.
