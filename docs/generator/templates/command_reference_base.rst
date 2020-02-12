.. _command_reference:

=================
Command reference
=================

Information on specific anonapi CLI functions. For more general information on how to achieve specific goals, see :doc:`usage`


.. note::
    Detailed help on commands is often available directly from the command line by adding ``--help`` to any command. See :ref:`getting_info_on_commands`

status
======

Display information on the command line tool itself. Which API servers it knows about, current active server


.. _server_commands:

server
======
Work with Anonymization server API servers. Add, remove servers, set active server

Overview of server functions:

{{ context.tables.root.server }}

.. _job:

job
===
Work with single jobs. Get extended info, reset, restart a job

Overview of job functions:

{{ context.tables.root.job }}


settings
========
Local settings for this anonapi instance. Credentials that are used to communicate with the API.


.. _batch:


batch
=====
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

{{ context.tables.root.batch }}


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


.. _map:

map
===
Create a mapping between data and anonymization parameters. This mapping contains everything needed to create
anonymization jobs

Overview of map functions:

{{ context.tables.root.map }}

add-all-study-folders
---------------------

Add all folders that match a pattern to mapping. The pattern can include ``*`` to match part of a file or folder,
and ``**`` to match any combination of folders and filenames.

For example, given the following folder structure::

    root
    |--patient1
    |   |--notes.txt
    |   |--raw
    |       |--raw1.dcm
    |       |--raw2.dcm
    |--patient2
    |   |--notes.txt
    |   |--test
    |       |--test.dcm
    |       |--othertest.dcm
    |       |--raw
    |           |--test2.dcm
    |   |--raw
    |       |--raw1.dcm
    |       |--raw2.dcm
    |       |--raw3.dcm


The following paths would be selected:

.. code-block:: console

    $ anon map add-all-study-folders */raw  #  match all direct subfolders named 'raw'
    > Pattern '*/raw' matches the following paths:
    > patient1/raw
    > patient2/raw

    $ anon map add-all-study-folders */*    #  match any direct subfolders
    > Pattern '*/*' matches the following paths:
    > patient1/raw
    > patient2/test
    > patient2/raw

    $ anon map add-all-study-folders **/raw  # match any subfolder named 'raw', at any depth
    > Pattern '*/raw' matches the following paths:
    > patient1/raw
    > patient2/test/raw
    > patient2/raw

    # tip: On linux terminals, the pattern currently needs to be quoted to avoid automatic expansion

.. note::

    Make sure that each added path contains data for only one patient. You can only map one patient name and id
    to each path.


.. _select:

select
======
select files for a single anonymization job


Overview of select functions:

{{ context.tables.root.select }}


.. _create:

create
======
create jobs


Overview of create functions:

{{ context.tables.root.create }}
