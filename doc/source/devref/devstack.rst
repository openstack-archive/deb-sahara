Setup DevStack
==============

The DevStack could be installed on Fedora, Ubuntu and CentOS. For supported
versions see `DevStack documentation <http://devstack.org>`_

We recommend to install DevStack not into your main system, but run it in
a VM instead. That way you may avoid contamination of your system
with various stuff. You may find hypervisor and VM requirements in the
the next section. If you still want to install DevStack on top of your
main system, just skip the next section and read further.


Start VM and set up OS
----------------------

In order to run DevStack in a local VM, you need to start by installing
a guest with Ubuntu 12.04 server. Download an image file from
`Ubuntu's web site <http://www.ubuntu.com/download/server>`_ and create
a new guest from it. Virtualization solution must support
nested virtualization. Without nested virtualization VMs running inside
the DevStack will be extremely slow lacking hardware acceleration, i.e.
you will run QEMU VMs without KVM.

On Linux QEMU/KVM supports nested virtualization, on Mac OS - VMware Fusion.
VMware Fusion requires adjustments to run VM with fixed IP. You may find
instructions which can help :ref:`below <fusion-fixed-ip>`.

Start a new VM with Ubuntu Server 12.04. Recommended settings:

- Processor - at least 2 cores
- Memory - at least 8GB
- Hard Drive - at least 60GB

When allocating CPUs and RAM to the DevStack, assess how big clusters you
want to run. A single Hadoop VM needs at least 1 cpu and 1G of RAM to run.
While it is possible for several VMs to share a single cpu core, remember
that they can't share the RAM.

After you installed the VM, connect to it via SSH and proceed with the
instructions below.


Install DevStack
----------------

The instructions assume that you've decided to install DevStack into
Ubuntu 12.04 system.

1. Clone DevStack:

.. sourcecode:: console

    $ sudo apt-get install git-core
    $ git clone https://git.openstack.org/cgit/openstack-dev/devstack.git

2. Create file ``local.conf`` in devstack directory with the following content:

.. sourcecode:: bash

    [[local|localrc]]
    ADMIN_PASSWORD=nova
    MYSQL_PASSWORD=nova
    RABBIT_PASSWORD=nova
    SERVICE_PASSWORD=$ADMIN_PASSWORD
    SERVICE_TOKEN=nova

    # Enable Swift
    enable_service s-proxy s-object s-container s-account

    SWIFT_HASH=66a3d6b56c1f479c8b4e70ab5c2000f5
    SWIFT_REPLICAS=1
    SWIFT_DATA_DIR=$DEST/data

    # Force checkout prerequisites
    # FORCE_PREREQ=1

    # keystone is now configured by default to use PKI as the token format which produces huge tokens.
    # set UUID as keystone token format which is much shorter and easier to work with.
    KEYSTONE_TOKEN_FORMAT=UUID

    # Change the FLOATING_RANGE to whatever IPs VM is working in.
    # In NAT mode it is subnet VMware Fusion provides, in bridged mode it is your local network.
    # But only use the top end of the network by using a /27 and starting at the 224 octet.
    FLOATING_RANGE=192.168.55.224/27

    # Enable auto assignment of floating IPs. By default Sahara expects this setting to be enabled
    EXTRA_OPTS=(auto_assign_floating_ip=True)

    # Enable logging
    SCREEN_LOGDIR=$DEST/logs/screen

    # Set ``OFFLINE`` to ``True`` to configure ``stack.sh`` to run cleanly without
    # Internet access. ``stack.sh`` must have been previously run with Internet
    # access to install prerequisites and fetch repositories.
    # OFFLINE=True

    # Enable Sahara
    enable_service sahara

3. Sahara can send notifications to Ceilometer, if Ceilometer is enabled.
   If you want to enable Ceilometer add the following lines to ``local.conf`` file:

.. sourcecode:: bash

    enable_service ceilometer-acompute ceilometer-acentral ceilometer-anotification ceilometer-collector
    enable_service ceilometer-alarm-evaluator,ceilometer-alarm-notifier
    enable_service ceilometer-api

4. Start DevStack:

.. sourcecode:: console

    $ ./stack.sh

5. Once previous step is finished Devstack will print Horizon URL. Navigate to
   this URL and login with login "admin" and password from ``local.conf``.

6. Congratulations! You have OpenStack running in your VM and ready to launch VMs inside that VM :)


Managing Sahara in DevStack
---------------------------

If you install DevStack with Sahara included you can rejoin screen with
``rejoin-stack.sh`` command and switch to ``sahara`` tab. Here you can manage
the Sahara service as other OpenStack services. Sahara source code is located
at ``$DEST/sahara`` which is usually ``/opt/stack/sahara``.


.. _fusion-fixed-ip:

Setting fixed IP address for VMware Fusion VM
---------------------------------------------

1. Open file ``/Library/Preferences/VMware Fusion/vmnet8/dhcpd.conf``
2. There is a block named "subnet". It might look like this:

.. sourcecode:: text

    subnet 192.168.55.0 netmask 255.255.255.0 {
            range 192.168.55.128 192.168.55.254;

3. You need to pick an IP address outside of that range. For example - ``192.168.55.20``
4. Copy VM MAC address from VM settings->Network->Advanced
5. Append the following block to file ``dhcpd.conf`` (don't forget to replace ``VM_HOSTNAME`` and ``VM_MAC_ADDRESS`` with actual values):

.. sourcecode:: text

    host VM_HOSTNAME {
            hardware ethernet VM_MAC_ADDRESS;
            fixed-address 192.168.55.20;
    }

6. Now quit all the VmWare Fusion applications and restart vmnet:

.. sourcecode:: console

    $ sudo /Applications/VMware\ Fusion.app/Contents/Library/vmnet-cli --stop
    $ sudo /Applications/VMware\ Fusion.app/Contents/Library/vmnet-cli --start

7. Now start your VM, it should have new fixed IP address
