Sahara Cluster Statuses Overview
================================

All Sahara Cluster operations are performed in multiple steps. A Cluster object
has a ``Status`` attribute which changes when Sahara finishes one step of
operations and starts another one. Also a Cluster object has a ``Status description``
attribute which changes each time when some error with the Cluster occurs.

Sahara supports three types of Cluster operations:
 * Create a new Cluster
 * Scale/Shrink an existing Cluster
 * Delete an existing Cluster

Creating a new Cluster
----------------------

1. Validating
~~~~~~~~~~~~~

Before performing any operations with OpenStack environment, Sahara validates
user input.

There are two types of validations, that are done:
 * Check that a request contains all necessary fields and that the request does not violate
any constraints like unique naming, etc.
 * Plugin check (optional). The provisioning Plugin may also perform any specific checks like Cluster topology validation.

If any of the validations fails during creating, the Cluster will
still be kept in the database with an ``Error`` status. If any validations fails during scaling the ``Active`` Cluster, it will be
kept with an ``Active`` status.
In both cases status description will contain message about the reasons of failure.

2. InfraUpdating
~~~~~~~~~~~~~~~~

This status means that the Provisioning plugin performs some infrastructural updates.

3. Spawning
~~~~~~~~~~~

Sahara sends requests to OpenStack for all resources to be created:
 * VMs
 * Volumes
 * Floating IPs (if Sahara is configured to use Floating IPs)

It takes some time for OpenStack to schedule all the required VMs and Volumes,
so Sahara will wait until all of them are in an ``Active`` state.

4. Waiting
~~~~~~~~~~

Sahara waits while VMs' operating systems boot up and all internal infrastructure
components like networks and volumes are attached and ready to use.

5. Preparing
~~~~~~~~~~~~

Sahara prepares a Cluster for starting. This step includes generating the ``/etc/hosts``
file, so that all instances can access each other by a hostname. Also Sahara
updates the ``authorized_keys`` file on each VM, so that communication can be done
without passwords.

6. Configuring
~~~~~~~~~~~~~~

Sahara pushes service configurations to VMs. Both XML based configurations and
environmental variables are set on this step.

7. Starting
~~~~~~~~~~~

Sahara is starting Hadoop services on Cluster's VMs.

8. Active
~~~~~~~~~

Active status means that a Cluster has started successfully and is ready to run Jobs.


Scaling/Shrinking an existing Cluster
-------------------------------------

1. Validating
~~~~~~~~~~~~~

Sahara checks the scale/shrink request for validity. The Plugin method called
for performing Plugin specific checks is different from creation validation method.

2. Scaling
~~~~~~~~~~

Sahara performs database operations updating all affected existing Node Groups
and creating new ones.

3. Adding Instances
~~~~~~~~~~~~~~~~~~~

State similar to ``Spawning`` while Custer creation. Sahara adds required amount
of VMs to existing Node Groups and creates new Node Groups.

4. Configuring
~~~~~~~~~~~~~~

State similar to ``Configuring`` while Cluster creation. New instances are being configured
in the same manner as already existing ones. Existing Cluster VMs are also updated
with a new ``/etc/hosts`` file.

5. Decommissioning
~~~~~~~~~~~~~~~~~~

Sahara stops Hadoop services on VMs that will be deleted from a Cluster.
Decommissioning a Data Node may take some time because Hadoop rearranges data replicas
around the Cluster, so that no data will be lost after that VM is deleted.

6. Deleting Instances
~~~~~~~~~~~~~~~~~~~~~

Sahara sends requests to OpenStack to release unneeded resources:
 * VMs
 * Volumes
 * Floating IPs (if they are used)

7. Active
~~~~~~~~~

The same ``Active`` as after Cluster creation.


Deleting an existing Cluster
----------------------------

1. Deleting
~~~~~~~~~~~

The only step, that releases all Cluster's resources and removes it from the database.

Error State
-----------

If the Cluster creation fails, the Cluster will get into an ``Error`` state.
This state means the Cluster may not be able to perform any operations normally.
This cluster will stay in the database until it is manually deleted. The reason for
failure may be found in the Sahara logs. Also status description will contain short
information about reasons of failure.


If an error occurs during the ``Adding Instances`` operation, Sahara will first
try to rollback this operation. If a rollback is impossible or fails itself, then
the Cluster will also go into an ``Error`` state. If a rollback was successful, Cluster will get into an ``Active`` state
and status description will contain short message about the reasons of ``Adding Instances`` failure.
