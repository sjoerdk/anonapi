===============
Getting started
===============

.. _installation:

Installation
============
.. highlight:: shell


To install AnonAPI, run this command in a :ref:`command prompt<usage_starting_a_command_prompt>`:

.. code-block:: console

    $ pip install anonapi

This is the preferred method to install AnonAPI, as it will always install the most recent stable release.

If you don't have `pip`_ installed, this `Python installation guide`_ can guide
you through the process.

.. _pip: https://pip.pypa.io
.. _Python installation guide: http://docs.python-guide.org/en/latest/starting/installation/


If you installed anonapi before and want to upgrade to the latest version:

.. code-block:: console

    $ pip install --upgrade anonapi



.. _configuration:

Configuration
=============

The Command Line Interface (CLI) needs to know a few things before it can be used.

.. _add_a_server_to_CLI:

Add a server to the CLI
-----------------------
The CLI communicates with one or more API servers. At least one of these should be added using the following steps:

First Find the url of an IDIS anonymization web API. An overview of servers within the radboudumc can be found
`here <https://repos.diagnijmegen.nl/trac/wiki/IDIS_web_API#servers>`_.

Lets say the server address is https://anonapi.org/server1. you can now add this server as 'server1':

.. code-block:: console

    $ anon server add server1 https://anonapi.org/server1

You can now see the new server in the server list:

.. code-block:: console

    $ anon server list

Activate server1. All subsequent commands will use this server.

.. code-block:: console

    $ anon server activate server1

.. _configure_credentials:

Configure credentials
---------------------
To make calls to any IDIS web API, the CLI needs to know which credentials to use. Do the following:

Set your username. For radboudumc this is your z-number. To set z1234567 as your username:

.. code-block:: console

    $ anon settings user set-username z1234567

Obtain an API token. This might require your z-number password)

.. code-block:: console

    $ anon settings user get-token
