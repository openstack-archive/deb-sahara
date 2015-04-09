Sahara Advanced Configuration Guide
===================================

This guide addresses specific aspects of Sahara configuration that pertain to
advanced usage. It is divided into sections about various features that can be
utilized, and their related configurations.

.. _custom_network_topologies:

Custom network topologies
-------------------------

Sahara accesses instances at several stages of cluster spawning through
SSH and HTTP. Floating IPs and network namespaces
(see :ref:`neutron-nova-network`) will be automatically used for
access when present. When floating IPs are not assigned to instances and
namespaces are not being used, sahara will need an alternative method to
reach them.

The ``proxy_command`` parameter of the configuration file can be used to
give sahara a command to access instances. This command is run on the
sahara host and must open a netcat socket to the instance destination
port. The ``{host}`` and ``{port}`` keywords should be used to describe the
destination, they will be substituted at runtime.  Other keywords that
can be used are: ``{tenant_id}``, ``{network_id}`` and ``{router_id}``.

For example, the following parameter in the sahara configuration file
would be used if instances are accessed through a relay machine:

.. sourcecode:: cfg

    [DEFAULT]
    proxy_command='ssh relay-machine-{tenant_id} nc {host} {port}'

Whereas the following shows an example of accessing instances though
a custom network namespace:

.. sourcecode:: cfg

    [DEFAULT]
    proxy_command='ip netns exec ns_for_{network_id} nc {host} {port}'

.. _data_locality_configuration:

Data-locality configuration
---------------------------

Hadoop provides the data-locality feature to enable task tracker and
data nodes the capability of spawning on the same rack, Compute node,
or virtual machine. Sahara exposes this functionality to the user
through a few configuration parameters and user defined topology files.

To enable data-locality, set the ``enable_data_locality`` parameter to
``True`` in the sahara configuration file

.. sourcecode:: cfg

    [DEFAULT]
    enable_data_locality=True

With data locality enabled, you must now specify the topology files
for the Compute and Object Storage services. These files are
specified in the sahara configuration file as follows:

.. sourcecode:: cfg

    [DEFAULT]
    compute_topology_file=/etc/sahara/compute.topology
    swift_topology_file=/etc/sahara/swift.topology

The ``compute_topology_file`` should contain mappings between Compute
nodes and racks in the following format:

.. sourcecode:: cfg

    compute1 /rack1
    compute1 /rack2
    compute1 /rack2

Note that the Compute node names must be exactly the same as configured in
OpenStack (``host`` column in admin list for instances).

The ``swift_topology_file`` should contain mappings between Object Storage
nodes and racks in the following format:

.. sourcecode:: cfg

    node1 /rack1
    node2 /rack2
    node3 /rack2

Note that the Object Storage node names must be exactly the same as
configured in the object ring. Also, you should ensure that instances
with the task tracker process have direct access to the Object Storage
nodes.

Hadoop versions after 1.2.0 support four-layer topology (for more detail
please see `HADOOP-8468 JIRA issue`_). To enable this feature set the
``enable_hypervisor_awareness`` parameter to ``True`` in the configuration
file. In this case sahara will add the Compute node ID as a second level of
topology for virtual machines.

.. _HADOOP-8468 JIRA issue: https://issues.apache.org/jira/browse/HADOOP-8468

.. _distributed-mode-configuration:

Distributed mode configuration
------------------------------

Sahara can be configured to run in a distributed mode that creates a
separation between the API and engine processes. This allows the API
process to remain relatively free to handle requests while offloading
intensive tasks to the engine processes.

The ``sahara-api`` application works as a front-end and serves user
requests. It offloads 'heavy' tasks to the ``sahara-engine`` process
via RPC mechanisms. While the ``sahara-engine`` process could be loaded
with tasks, ``sahara-api`` stays free and hence may quickly respond to
user queries.

If sahara runs on several hosts, the API requests could be
balanced between several ``sahara-api`` hosts using a load balancer.
It is not required to balance load between different ``sahara-engine``
hosts as this will be automatically done via the message broker.

If a single host becomes unavailable, other hosts will continue
serving user requests. Hence, a better scalability is achieved and some
fault tolerance as well. Note that distributed mode is not a true
high availability. While the failure of a single host does not
affect the work of the others, all of the operations running on
the failed host will stop. For example, if a cluster scaling is
interrupted, the cluster will be stuck in a half-scaled state. The
cluster might continue working, but it will be impossible to scale it
further or run jobs on it via EDP.

To run sahara in distributed mode pick several hosts on which
you want to run sahara services and follow these steps:

 * On each host install and configure sahara using the
   `installation guide <../installation.guide.html>`_
   except:

    * Do not run ``sahara-db-manage`` or launch sahara with ``sahara-all``
    * Ensure that each configuration file provides a database connection
      string to a single database for all hosts.

 * Run ``sahara-db-manage`` as described in the installation guide,
   but only on a single (arbitrarily picked) host.

 * The ``sahara-api`` and ``sahara-engine`` processes use oslo.messaging to
   communicate with each other. You will need to configure it properly on
   each host (see below).

 * Run ``sahara-api`` and ``sahara-engine`` on the desired hosts. You may
   run both processes on the same or separate hosts as long as they are
   configured to use the same message broker and database.

To configure oslo.messaging, first you will need to choose a message
broker driver. Currently there are three drivers provided: RabbitMQ, Qpid
or ZeroMQ. For the RabbitMQ or Qpid drivers please see the
:ref:`notification-configuration` documentation for an explanation of
common configuration options.

For an expanded view of all the options provided by each message broker
driver in oslo.messaging please refer to the options available in the
respective source trees:

 * For Rabbit MQ see

   * rabbit_opts variable in `impl_rabbit.py <https://git.openstack.org/cgit/openstack/oslo.messaging/tree/oslo/messaging/_drivers/impl_rabbit.py?id=1.4.0#n38>`_
   * amqp_opts variable in `amqp.py <https://git.openstack.org/cgit/openstack/oslo.messaging/tree/oslo/messaging/_drivers/amqp.py?id=1.4.0#n37>`_

 * For Qpid see

   * qpid_opts variable in `impl_qpid.py <https://git.openstack.org/cgit/openstack/oslo.messaging/tree/oslo/messaging/_drivers/impl_qpid.py?id=1.4.0#n40>`_
   * amqp_opts variable in `amqp.py <https://git.openstack.org/cgit/openstack/oslo.messaging/tree/oslo/messaging/_drivers/amqp.py?id=1.4.0#n37>`_

 * For Zmq see

   * zmq_opts variable in `impl_zmq.py <https://git.openstack.org/cgit/openstack/oslo.messaging/tree/oslo/messaging/_drivers/impl_zmq.py?id=1.4.0#n49>`_
   * matchmaker_opts variable in `matchmaker.py <https://git.openstack.org/cgit/openstack/oslo.messaging/tree/oslo/messaging/_drivers/matchmaker.py?id=1.4.0#n27>`_
   * matchmaker_redis_opts variable in `matchmaker_redis.py <https://git.openstack.org/cgit/openstack/oslo.messaging/tree/oslo/messaging/_drivers/matchmaker_redis.py?id=1.4.0#n26>`_
   * matchmaker_opts variable in `matchmaker_ring.py <https://git.openstack.org/cgit/openstack/oslo.messaging/tree/oslo/messaging/_drivers/matchmaker_ring.py?id=1.4.0#n27>`_

These options will also be present in the generated sample configuration
file. For instructions on creating the configuration file please see the
:doc:`configuration.guide`.

External key manager usage (EXPERIMENTAL)
-----------------------------------------

Sahara generates and stores several passwords during the course of operation.
To harden sahara's usage of passwords it can be instructed to use an
external key manager for storage and retrieval of these secrets. To enable
this feature there must first be an OpenStack Key Manager service deployed
within the stack. Currently, the barbican project is the only key manager
supported by sahara.

With a Key Manager service deployed on the stack, sahara must be configured
to enable the external storage of secrets. This is accomplished by editing
the sahara configuration file as follows:

.. sourcecode:: cfg

    [DEFAULT]
    use_external_key_manager=True

.. TODO (mimccune)
    this language should be removed once a new keystone authentication
    section has been created in the configuration file.

Additionally, at this time there are two more values which must be provided
to ensure proper access for sahara to the Key Manager service. These are
the Identity domain for the administrative user and the domain for the
administrative project. By default these values will appear as:

.. sourcecode:: cfg

    [DEFAULT]
    admin_user_domain_name=default
    admin_project_domain_name=default

With all of these values configured and the Key Manager service deployed,
sahara will begin storing its secrets in the external manager.

Indirect instance access through proxy nodes
--------------------------------------------

.. warning::
    The indirect VMs access feature is in alpha state. We do not
    recommend using it in a production environment.

Sahara needs to access instances through SSH during cluster setup. This
access can be obtained a number of different ways (see
:ref:`neutron-nova-network`, :ref:`floating_ip_management`,
:ref:`custom_network_topologies`). Sometimes it is impossible to provide
access to all nodes (because of limited numbers of floating IPs or security
policies). In these cases access can be gained using other nodes of the
cluster as proxy gateways. To enable this set ``is_proxy_gateway=True``
for the node group you want to use as proxy. Sahara will communicate with
all other cluster instances through the instances of this node group.

Note, if ``use_floating_ips=true`` and the cluster contains a node group with
``is_proxy_gateway=True``, the requirement to have ``floating_ip_pool``
specified is applied only to the proxy node group. Other instances will be
accessed through proxy instances using the standard private network.

Note, the Cloudera Hadoop plugin doesn't support access to Cloudera manager
through a proxy node. This means that for CDH clusters only nodes with
the Cloudera manager can be designated as proxy gateway nodes.

Multi region deployment
-----------------------

Sahara supports multi region deployment. To enable this option each
instance of sahara should have the ``os_region_name=<region>``
parameter set in the configuration file. The following example demonstrates
configuring sahara to use the ``RegionOne`` region:

.. sourcecode:: cfg

    [DEFAULT]
    os_region_name=RegionOne

.. _non-root-users:

Non-root users
--------------

In cases where a proxy command is being used to access cluster instances
(for example, when using namespaces or when specifying a custom proxy
command), rootwrap functionality is provided to allow users other than
``root`` access to the needed operating system facilities. To use rootwrap
the following configuration parameter is required to be set:

.. sourcecode:: cfg

    [DEFAULT]
    use_rootwrap=True


Assuming you elect to leverage the default rootwrap command
(``sahara-rootwrap``), you will need to perform the following additional setup
steps:

* Copy the provided sudoers configuration file from the local project file
  ``etc/sudoers.d/sahara-rootwrap`` to the system specific location, usually
  ``/etc/sudoers.d``. This file is setup to allow a user named ``sahara``
  access to the rootwrap script. It contains the following:

.. sourcecode:: cfg

    sahara ALL = (root) NOPASSWD: /usr/bin/sahara-rootwrap /etc/sahara/rootwrap.conf *


* Copy the provided rootwrap configuration file from the local project file
  ``etc/sahara/rootwrap.conf`` to the system specific location, usually
  ``/etc/sahara``. This file contains the default configuration for rootwrap.

* Copy the provided rootwrap filters file from the local project file
  ``etc/sahara/rootwrap.d/sahara.filters`` to the location specified in the
  rootwrap configuration file, usually ``/etc/sahara/rootwrap.d``. This file
  contains the filters that will allow the ``sahara`` user to access the
  ``ip netns exec``, ``nc``, and ``kill`` commands through the rootwrap
  (depending on ``proxy_command`` you may need to set additional filters).
  It should look similar to the followings:

.. sourcecode:: cfg

    [Filters]
    ip: IpNetnsExecFilter, ip, root
    nc: CommandFilter, nc, root
    kill: CommandFilter, kill, root

If you wish to use a rootwrap command other than ``sahara-rootwrap`` you can
set the following parameter in your sahara configuration file:

.. sourcecode:: cfg

    [DEFAULT]
    rootwrap_command='sudo sahara-rootwrap /etc/sahara/rootwrap.conf'

For more information on rootwrap please refer to the
`official Rootwrap documentation <https://wiki.openstack.org/wiki/Rootwrap>`_

Object Storage access using proxy users
---------------------------------------

To improve security for clusters accessing files in Object Storage,
sahara can be configured to use proxy users and delegated trusts for
access. This behavior has been implemented to reduce the need for
storing and distributing user credentials.

The use of proxy users involves creating an Identity domain that will be
designated as the home for these users. Proxy users will be
created on demand by sahara and will only exist during a job execution
which requires Object Storage access. The domain created for the
proxy users must be backed by a driver that allows sahara's admin user to
create new user accounts. This new domain should contain no roles, to limit
the potential access of a proxy user.

Once the domain has been created, sahara must be configured to use it by
adding the domain name and any potential delegated roles that must be used
for Object Storage access to the sahara configuration file. With the
domain enabled in sahara, users will no longer be required to enter
credentials for their data sources and job binaries referenced in
Object Storage.

Detailed instructions
^^^^^^^^^^^^^^^^^^^^^

First a domain must be created in the Identity service to hold proxy
users created by sahara. This domain must have an identity backend driver
that allows for sahara to create new users. The default SQL engine is
sufficient but if your keystone identity is backed by LDAP or similar
then domain specific configurations should be used to ensure sahara's
access. Please see the `Keystone documentation`_ for more information.

.. _Keystone documentation: http://docs.openstack.org/developer/keystone/configuration.html#domain-specific-drivers

With the domain created, sahara's configuration file should be updated to
include the new domain name and any potential roles that will be needed. For
this example let's assume that the name of the proxy domain is
``sahara_proxy`` and the roles needed by proxy users will be ``Member`` and
``SwiftUser``.

.. sourcecode:: cfg

    [DEFAULT]
    use_domain_for_proxy_users=True
    proxy_user_domain_name=sahara_proxy
    proxy_user_role_names=Member,SwiftUser

..

A note on the use of roles. In the context of the proxy user, any roles
specified here are roles intended to be delegated to the proxy user from the
user with access to Object Storage. More specifically, any roles that
are required for Object Storage access by the project owning the object
store must be delegated to the proxy user for authentication to be
successful.

Finally, the stack administrator must ensure that images registered with
sahara have the latest version of the Hadoop swift filesystem plugin
installed. The sources for this plugin can be found in the
`sahara extra repository`_. For more information on images or swift
integration see the sahara documentation sections
:ref:`diskimage-builder-label` and :ref:`swift-integration-label`.

.. _Sahara extra repository: http://github.com/openstack/sahara-extra

.. _volume_instance_locality_configuration:

Volume instance locality configuration
--------------------------------------

The Block Storage service provides the ability to define volume instance
locality to ensure that instance volumes are created on the same host
as the hypervisor. The ``InstanceLocalityFilter`` provides the mechanism
for the selection of a storage provider located on the same physical
host as an instance.

To enable this functionality for instances of a specific node group, the
``volume_local_to_instance`` field in the node group template should be
set to ``True`` and some extra configurations are needed:

* The cinder-volume service should be launched on every physical host and at
  least one physical host should run both cinder-scheduler and
  cinder-volume services.
* ``InstanceLocalityFilter`` should be added to the list of default filters
  (``scheduler_default_filters`` in cinder) for the Block Storage
  configuration.
* The Extended Server Attributes extension needs to be active in the Compute
  service (this is true by default in nova), so that the
  ``OS-EXT-SRV-ATTR:host`` property is returned when requesting instance
  info.
* The user making the call needs to have sufficient rights for the property to
  be returned by the Compute service.
  This can be done by:

  * by changing nova's ``policy.json`` to allow the user access to the
    ``extended_server_attributes`` option.
  * by designating an account with privileged rights in the cinder
    configuration:

    .. sourcecode:: cfg

        os_privileged_user_name =
        os_privileged_user_password =
        os_privileged_user_tenant =

It should be noted that in a situation when the host has no space for volume
creation, the created volume will have an ``Error`` state and can not be used.
