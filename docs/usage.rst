=====
Usage
=====

The anonapi package contains two distinct ways of interacting with an IDIS anonymization server.

    * :ref:`usage-cli` : for quick overview of jobs and cancel/restart.

    * :ref:`usage-client` : for creating, modifying and automation.


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

First Find the url of an IDIS anonymization web API. An overview of servers within the radboudumc can be found
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

WebAPIClient python class
=========================
:mod:`anonapi.client.WebAPIClient` is the main class to use when interacting with an IDIS server web API from python.
To use it in a python file:


.. code-block:: python

    from anonapi.client import WebAPIClient

    client = WebAPIClient(
        hostname="https://umcradanonp11.umcn.nl/sandbox",
        username="z123sandbox",
        token="token",
    )

    # Get some information on first few jobs
    jobs_info = client.get("get_jobs")

A more extended python example of creating, modifying and cancelling jobs can be found in the in
:ref:`examples`.
