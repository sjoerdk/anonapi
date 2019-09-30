=========
CLI Usage
=========

How to use the anonapi Command Line Interface (CLI)

    * :ref:`usage-cli-setup` : for quick overview of jobs and cancel/restart.

    * :ref:`usage-cli-reference` : for information on each CLI function

.. _usage-cli-setup:

Command Line Interface (CLI) setup
==================================
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


.. _usage-cli-reference:

Command Line Interface (CLI) reference
======================================

Overview of all CLI functions. For more information, use 'anon <function> -h' in the CLI itself

status
------
Display information on the command line tool itself. Which API servers it knows about, current active server.

.. code-block:: console

    $ anon status -h   # list all commands

server
------
Work with Anonymization server API servers. Add, remove servers, set active server.

.. code-block:: console

    $ anon server -h   # list all commands

job
---
Work with single jobs. Get extended info, reset, restart a job

.. code-block:: console

    $ anon job -h   # list all commands


user
----
Information and editing of credentials that are used to communicate with the API.

.. code-block:: console

    $ anon user -h   # list all commands


.. _batch:

batch
-----
Work with lists of jobs on a certain server. Anonymization jobs often occur in sets. With batches you can group
jobs together an do batch processing on them. A batch lives in a single folder. To work with a batch you have to be in
that folder. For example:

.. code-block:: console

    $ cd /tmp/my_folder
    $ anon batch info  # Will not work because there is no batch defined in this folder yet
    > Error: No batch defined in current folder

    $ anon batch init  # Create empty batch for the currently active server
    > Initialised batch for p01: https://apiservers/p01 in current dir

    $ anon batch info  # Now there is an empty list
    >  job_ids: []
        server:
          name: p01
          url: https://apiservers/p01

    $ anon batch add 1 2 3 # Now you can add job ids, separated by spaces
    $ anon batch info  # Now there is an empty list
    >  job_ids: ['1', '2', '3' ]
        server:
          name: p01
          url: https://apiservers/p01

    $ anon batch status  # Now you can print status for all ids in this batch
    > Job info for 3 jobs on p01: https://umcradanonp11.umcn.nl/p01:

          id     date                 status   downloaded processed  user
          ---------------------------------------------------------------
          1      2016-08-26T15:04:44  INACTIVE 0          0          z123456
          2      2016-08-26T15:04:44  ERROR    503        100        z123456
          3      2016-08-26T15:04:44  DONE     1155       1155       z123456


batch command overview:

============        ====================================================
Command             Description
============        ====================================================
info                print overview of all jobs in current folder
status              get_status for entire batch
reset               reset every job in this batch
init                Create empty batch in current folder
delete              Delete batch in current folder
add                 Add job ids to batch
remove              Remove job ids from batch
cancel              Cancel all jobs in this batch
reset_error         Reset all jobs with error status in current batch
============        ====================================================


For convenience, it is possible to pass job ids for batch add and batch remove as ranges:

.. code-block:: console

    $ anon batch add 5-12 # Add range
    $ anon batch info  # ranges include both start and end number
    >  job_ids: ['5', '6', '7', '8', '9', '10', '11', '12']
        server:
          name: p01
          url: https://apiservers/p01

    $ anon batch remove 8-11 # Remove range
    $ anon batch info  # ranges include both start and end number
    >  job_ids: ['5', '6', '7', '12']
        server:
          name: p01
          url: https://apiservers/p01

