Sahara Upgrade Guide
====================

This page contains details about upgrading sahara between releases such
as configuration file updates, database migrations, and architectural
changes.

Icehouse -> Juno
----------------

Main binary renamed to sahara-all
+++++++++++++++++++++++++++++++++

The All-In-One sahara binary has been renamed from ``sahara-api``
to ``sahara-all``. The new name should be used in all cases where the
All-In-One sahara is desired.

Authentication middleware changes
+++++++++++++++++++++++++++++++++

The custom auth_token middleware has been deprecated in favor of the
keystone middleware. This change requires an update to the sahara
configuration file. To update your configuration file you should replace
the following parameters from the ``[DEFAULT]`` section with the new
parameters in the ``[keystone_authtoken]`` section:

+----------------------+--------------------+
| Old parameter name   | New parameter name |
+======================+====================+
| os_admin_username    | admin_user         |
+----------------------+--------------------+
| os_admin_password    | admin_password     |
+----------------------+--------------------+
| os_admin_tenant_name | admin_tenant_name  |
+----------------------+--------------------+

Additionally, the parameters ``os_auth_protocol``, ``os_auth_host``,
and ``os_auth_port`` have been combined to create the ``auth_uri``
and ``identity_uri`` parameters. These new parameters should be
full URIs to the keystone public and admin endpoints, respectively.

For more information about these configuration parameters please see
the :doc:`configuration.guide`.

Database package changes
++++++++++++++++++++++++

The oslo based code from sahara.openstack.common.db has been replaced by
the usage of the oslo.db package. This change does not require any
update to sahara's configuration file.

Additionally, the usage of SQLite databases has been deprecated. Please
use MySQL or PostgreSQL databases for sahara. SQLite has been
deprecated because it does not, and is not going to, support the
``ALTER COLUMN`` and ``DROP COLUMN`` commands required for migrations
between versions. For more information please see
http://www.sqlite.org/omitted.html

Sahara integration into OpenStack Dashboard
+++++++++++++++++++++++++++++++++++++++++++

The sahara dashboard package has been deprecated in the Juno release. The
functionality of the dashboard has been fully incorporated into the
OpenStack Dashboard. The sahara interface is available under the
"Project" -> "Data Processing" tab.

The Data processing service endpoints must be registered in the Identity
service catalog for the Dashboard to properly recognize and display
those user interface components. For more details on this process please see
:ref:`registering Sahara in installation guide <register-sahara-label>`.

The
`sahara-dashboard <https://git.openstack.org/cgit/openstack/sahara-dashboard>`_
project is now used solely to host sahara user interface integration tests.

Virtual machine user name changes
+++++++++++++++++++++++++++++++++

The HEAT infrastructure engine has been updated to use the same rules for
instance user names as the direct engine. In previous releases the user
name for instances created by sahara using HEAT was always 'ec2-user'. As
of Juno, the user name is taken from the image registry as described in
the :doc:`registering_image` document.

This change breaks backward compatibility for clusters created using the
HEAT infrastructure engine prior to the Juno release. Clusters will
continue to operate, but we do not recommended using the scaling operations
with them.

Anti affinity implementation changed
++++++++++++++++++++++++++++++++++++

Starting with the Juno release the anti affinity feature is implemented
using server groups. From the user prespective there will be no
noticeable changes with this feature. Internally this change has
introduced the following behavior:

1) Server group objects will be created for any clusters with anti affinity
   enabled.
2) Affected instances on the same host will not be allowed even if they
   do not have common processes. Prior to Juno, instances with differing
   processes were allowed on the same host. The new implementation
   guarantees that all affected instances will be on different hosts
   regardless of their processes.

The new anti affinity implementation will only be applied for new clusters.
Clusters created with previous versions will continue to operate under
the older implementation, this applies to scaling operations on these
clusters as well.

Juno -> Kilo
------------

Sahara requires policy configuration
++++++++++++++++++++++++++++++++++++

Sahara now requires a policy configuration file. The ``policy.json`` file
should be placed in the same directory as the sahara configuration file or
specified using the ``policy_file`` parameter. For more details about the
policy file please see the
:ref:`policy section in the configuration guide <policy-configuration-label>`.
