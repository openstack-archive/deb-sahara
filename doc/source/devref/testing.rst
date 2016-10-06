Sahara Testing
==============

We have a bunch of different tests for Sahara.

Unit Tests
++++++++++

In most Sahara sub-repositories we have a directory that contains Python unit
tests, located at `_package_/tests/unit` or `_package_/tests`.

Scenario integration tests
++++++++++++++++++++++++++

New scenario integration tests were implemented for Sahara. They are available
in the sahara-tests repository
(https://git.openstack.org/cgit/openstack/sahara-tests).

Tempest tests
+++++++++++++

Sahara has a Tempest plugin in the sahara-tests repository covering all major
API features.

Additional tests
++++++++++++++++

Additional tests reside in the sahara-tests repository (as above):

* REST API tests checking to ensure that the Sahara REST API works.
  The only parts that are not tested are cluster creation and EDP. For more
  info about api tests see
  http://docs.openstack.org/developer/tempest/field_guide/api.html

* CLI tests check read-only operations using the Sahara CLI. For more info see
  http://docs.openstack.org/developer/tempest/field_guide/cli.html
