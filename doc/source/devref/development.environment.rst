Setting Up a Development Environment
====================================

This page describes how to setup a Sahara development environment by either
installing it as a part of DevStack or pointing a local running instance at an
external OpenStack. You should be able to debug and test your changes without
having to deploy Sahara.

Setup a Local Environment with Sahara inside DevStack
-----------------------------------------------------

See :doc:`the main article <devstack>`.

Setup a Local Environment with an external OpenStack
----------------------------------------------------

1. Install prerequisites

On OS X Systems:

.. sourcecode:: console

    # we actually need pip, which is part of python package
    $ brew install python mysql postgresql
    $ pip install virtualenv tox

On Ubuntu:

.. sourcecode:: console

    $ sudo apt-get update
    $ sudo apt-get install git-core python-dev python-virtualenv gcc libpq-dev libmysqlclient-dev python-pip
    $ sudo pip install tox

On Fedora-based distributions (e.g., Fedora/RHEL/CentOS/Scientific Linux):

.. sourcecode:: console

    $ sudo yum install git-core python-devel python-virtualenv gcc python-pip mariadb-devel postgresql-devel
    $ sudo pip install tox

On openSUSE-based distributions (SLES 12, openSUSE, Factory or Tumbleweed)::

.. sourcecode:: console

    $ sudo zypper in gcc git libmysqlclient-devel postgresql-devel python-devel python-pip python-tox python-virtualenv

2. Grab the code:

.. sourcecode:: console

    $ git clone git://github.com/openstack/sahara.git
    $ cd sahara

3.1 Generate Sahara sample using tox:

.. sourcecode:: console

   tox -e genconfig

3.2 Create config file from the sample:

.. sourcecode:: console

    $ cp ./etc/sahara/sahara.conf.sample ./etc/sahara/sahara.conf

4. Look through the sahara.conf and modify parameter values as needed.
   For details see
   :doc:`Sahara Configuration Guide </userdoc/configuration.guide>`

5. Create database schema:

.. sourcecode:: console

    $ tox -e venv -- sahara-db-manage --config-file etc/sahara/sahara.conf upgrade head

6. To start Sahara call:

.. sourcecode:: console

    $ tox -e venv -- sahara-all --config-file etc/sahara/sahara.conf --debug


Setup local OpenStack dashboard with Sahara plugin
--------------------------------------------------

.. toctree::
    :maxdepth: 1


    ../horizon/dev.environment.guide

Tips and tricks for dev environment
-----------------------------------

1. Pip speedup

Add the following lines to ~/.pip/pip.conf

.. sourcecode:: cfg

    [global]
    download-cache = /home/<username>/.pip/cache
    index-url = <mirror url>

Note that the ``~/.pip/cache`` folder should be created manually.

2. Git hook for fast checks

Just add the following lines to .git/hooks/pre-commit and do chmod +x for it.

.. sourcecode:: console

    #!/bin/sh
    # Run fast checks (PEP8 style check and PyFlakes fast static analysis)
    tools/run_fast_checks

You can added the same check for pre-push, for example, run_tests and run_pylint.

3. Running static analysis (PyLint)

Just run the following command

.. sourcecode:: console

    tox -e pylint
