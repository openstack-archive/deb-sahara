Development Guidelines
======================

Coding Guidelines
-----------------

For all the Python code in Sahara we have a rule - it should pass `PEP 8`_.
All Bash code should pass `bashate`_.

To check your code against PEP 8 and bashate run:

.. sourcecode:: console

    $ tox -e pep8

.. note::
  For more details on coding guidelines see file ``HACKING.rst`` in the root
  of Sahara repo.

Static analysis
---------------

The static analysis checks are optional in Sahara. but they are still very
useful.  The gate job will inform you if the number of static analysis warnings
has increased after your change. We recommend to always check the static
warnings.

To run the check commit yor change first and execute the following command:

.. sourcecode:: console

    $ tox -e pylint

Modification of Upstream Files
------------------------------

We never modify upstream files in Sahara. Any changes in upstream files should
be made in the upstream project and then merged back in to Sahara.  This
includes whitespace changes, comments, and typos. Any change requests
containing upstream file modifications are almost certain to receive lots of
negative reviews.  Be warned.

Examples of upstream files are default xml configuration files used to
configure Hadoop, or code imported from the OpenStack Oslo project. The xml
files will usually be found in ``resource`` directories with an accompanying
``README`` file that identifies where the files came from.  For example:

.. sourcecode:: console

  $ pwd
  /home/me/sahara/sahara/plugins/vanilla/v2_7_1/resources

  $ ls
  core-default.xml     hdfs-default.xml    oozie-default.xml   README.rst
  create_oozie_db.sql  mapred-default.xml  post_conf.template  yarn-default.xml
..

Testing Guidelines
------------------

Sahara has a suite of tests that are run on all submitted code,
and it is recommended that developers execute the tests themselves to
catch regressions early.  Developers are also expected to keep the
test suite up-to-date with any submitted code changes.

Unit tests are located at ``sahara/tests/unit``.

Sahara's suite of unit tests can be executed in an isolated environment
with `Tox`_. To execute the unit tests run the following from the root of
Sahara repo:

.. sourcecode:: console

    $ tox -e py27


Documentation Guidelines
------------------------

All Sahara docs are written using Sphinx / RST and located in the main repo
in ``doc`` directory. You can add/edit pages here to update
http://docs.openstack.org/developer/sahara site.

The documentation in docstrings should follow the `PEP 257`_ conventions
(as mentioned in the `PEP 8`_ guidelines).

More specifically:

1. Triple quotes should be used for all docstrings.
2. If the docstring is simple and fits on one line, then just use
   one line.
3. For docstrings that take multiple lines, there should be a newline
   after the opening quotes, and before the closing quotes.
4. `Sphinx`_ is used to build documentation, so use the restructured text
   markup to designate parameters, return values, etc.  Documentation on
   the sphinx specific markup can be found here:



Run the following command to build docs locally.

.. sourcecode:: console

    $ tox -e docs

After it you can access generated docs in ``doc/build/`` directory, for
example, main page - ``doc/build/html/index.html``.

To make docs generation process faster you can use:

.. sourcecode:: console

    $ SPHINX_DEBUG=1 tox -e docs

or to avoid sahara reinstallation to virtual env each time you want to rebuild
docs you can use the following command (it could be executed only after
running ``tox -e docs`` first time):

.. sourcecode:: console

    $ SPHINX_DEBUG=1 .tox/docs/bin/python setup.py build_sphinx



.. note::
  For more details on documentation guidelines see file HACKING.rst in the root
  of Sahara repo.


.. _PEP 8: http://www.python.org/dev/peps/pep-0008/
.. _bashate: https://github.com/openstack-dev/bashate
.. _PEP 257: http://www.python.org/dev/peps/pep-0257/
.. _Tox: http://tox.testrun.org/
.. _Sphinx: http://sphinx.pocoo.org/markup/index.html

Event log Guidelines
--------------------

Currently Sahara keep with cluster useful information about provisioning.
Cluster provisioning can be represented as a linear series of provisioning
steps, which are executed one after another. Also each step would consist of
several events. The amount of events depends on the step and the amount of
instances in the cluster. Also each event can contain information about
cluster, instance, and node group. In case of errors, this event would contain
information about reasons of errors. Each exception in sahara contains a
unique identifier that will allow the user to find extra information about
the reasons for errors in the sahara logs. Here
http://developer.openstack.org/api-ref-data-processing-v1.1.html#v1.1eventlog
you can see an example of provisioning progress information.

This means that if you add some important phase for cluster provisioning to
sahara code, it's recommended to add new provisioning step for this phase.
It would allow users to use event log for handling errors during this phase.

Sahara already have special utils for operating provisioning steps and events
in module ``sahara/utils/cluster_progress_ops.py``.

.. note::
    It's strictly recommended not use ``conductor`` event log ops directly
    to assign events and operate provisioning steps.

.. note::
    You should not add a new provisioning step until the previous step
    successfully completed.

.. note::
    It's strictly recommended to use ``event_wrapper`` for events handling

OpenStack client usage guidelines
---------------------------------

The sahara project uses several OpenStack clients internally. These clients
are all wrapped by utility functions which make using them more convenient.
When developing sahara, if you need to use a OpenStack client you should
check the ``sahara.utils.openstack`` package for the appropriate one.

When developing new OpenStack client interactions in sahara, it is important
to understand the ``sahara.service.sessions`` package and the usage of
keystone ``Session`` and auth plugin objects(for example, ``Token`` or
``Password``). Sahara is migrating all clients to use this authentication
methodology, where available. For more information on using sessions with
keystone, please see
http://docs.openstack.org/developer/keystoneauth/using-sessions.html

Storing sensitive information
-----------------------------

During the course of development, there is often cause to store sensitive
information (for example, login credentials) in the records for a cluster,
job, or some other record. Storing secret information this way is **not**
safe. To mitigate the risk of storing this information, sahara provides
access to the OpenStack Key Manager service (implemented by the
`barbican project <http://docs.openstack.org/developer/barbican/>`_) through
the `castellan library <http://docs.openstack.org/developer/castellan/>`_.

To utilize the external key manager, the functions in
``sahara.service.castellan.utils`` are provided as wrappers around the
castellan library. These functions allow a developer to store, retrieve, and
delete secrets from the manager. Secrets that are managed through the key
manager have an identifier associated with them. These identifiers are
considered safe to store in the database.

The following are some examples of working with secrets in the sahara
codebase. These examples are considered basic, any developer wishing to
learn more about the advanced features of storing secrets should look to
the code and docstrings contained in the ``sahara.service.castellan`` module.

**Storing a secret**

.. sourcecode:: python

    from sahara.service.castellan import utils as key_manager

    password = 'SooperSecretPassword'
    identifier = key_manager.store_secret(password)

**Retrieving a secret**

.. sourcecode:: python

    from sahara.service.castellan import utils as key_manager

    password = key_manager.get_secret(identifier)

**Deleting a secret**

.. sourcecode:: python

    from sahara.service.castellan import utils as key_manager

    key_manager.delete_secret(identifier)

When storing secrets through this interface it is important to remember that
if an external key manager is being used, each stored secret creates an
entry in an external service. When you are finished using the secret it is
good practice to delete it, as not doing so may leave artifacts in those
external services.

For more information on configuring sahara to use the OpenStack Key
Manager service, see :ref:`external_key_manager_usage`.
