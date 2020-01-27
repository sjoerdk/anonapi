.. _command_reference:

Command reference
=================

Overview of all CLI functions. For more information, type 'anon <function>' and press enter in the CLI itself

status
------
Display information on the command line tool itself. Which API servers it knows about, current active server

.. code-block:: console

    $ anon status   # list all commands

.. _server_commands:

server
------
Work with Anonymization server API servers. Add, remove servers, set active server

.. code-block:: console

    $ anon server   # list all commands

job
---
Work with single jobs. Get extended info, reset, restart a job

.. code-block:: console

    $ anon job   # list all commands


settings
--------
Local settings for this anonapi instance. Credentials that are used to communicate with the API, path mapping etc.

.. code-block:: console

    $ anon settings user   # list all commands


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
