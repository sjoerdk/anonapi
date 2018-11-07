=====
Usage
=====

The anonapi package contains two distinct ways of interacting with an IDIS anonymization server API:

    * The command line interface 'anon', used for quick overview of jobs and cancel/restart (See :ref:`usage-cli`).

    * The Web API Python client classes, for creating, modifying and automating job creation (see :ref:`usage-client`).


Prerequisites
-------------

    * python 3.6

    * pip


.. _usage-cli:

Command Line Interface (CLI)
============================
After :doc:`installation` you can use the CLI from any terminal via the keyword 'anon':

.. code-block:: console

    $ anon           # prints basic usage information

    $ anon status    # prints current configuration


CLI Commands
------------
use -h for help on any CLI command or subcommand. For example:

.. code-block:: console

    $ anon -h   # print overview of commands

    $ anon server -h   # print overview of all server subcommands


Add a server to the CLI
-----------------------
The CLI saves server locations locally for easy access. To add a server follow these steps:

First Find the url of an IDIS anonymization web API. An overview of servers without the radboudumc can found
`here <https://repos.diagnijmegen.nl/trac/wiki/IDIS_web_API#servers>`_.

Lets say the server address is https://anonapi.org/server1. you can now add this server as 'server1':

.. code-block:: console

    $ anon server add server1 https://anonapi.org/server1

See a list of all servers known locally

.. code-block:: console

    $ anon server list

Activate server1. All subsequent commands will use this server.

.. code-block:: console

    $ anon server activate server1


Configure credentials
---------------------
To make calls to any IDIS web API, the CLI needs to know which credentials to use. Do the following:

Set your username. For radboudumc this is your z-number. To set z1234567 as your username:

.. code-block:: console

    $ anon user set_username z1234567

Obtain an API token. This might require your z-number password)

.. code-block:: console

    $ anon user get_token


Example commands
----------------
.. code-block:: console


    $ anon server jobs  # Show 50 most recent jobs on server

    $ anon job info 123  # Print extended info on job 123

    $ anon job cancel 123  # Cancel job 123

    $ anon job reset 123  # Restart job 123


.. _usage-client:

Web API Python client
=====================
