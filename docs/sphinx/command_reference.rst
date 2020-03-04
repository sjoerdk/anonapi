.. _command_reference:

=================
Command reference
=================

Information on specific anonapi CLI functions. For more how-to's on achieving specific goals, see :doc:`usage`


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

======== ========================================================================
Command  Description                                                             
======== ========================================================================
activate Commands will use given server by default                               
add      Add a server to the list of servers in settings                         
jobs     List latest 100 jobs for active server                                  
list     show all servers in settings                                            
remove   Remove a server from list in settings                                   
status   Check whether active server is online and responding                    
======== ========================================================================

.. _job:

job
===
Work with single jobs. Get extended info, reset, restart a job

Overview of job functions:

======= =========================================================================
Command Description                                                              
======= =========================================================================
cancel  set job status to inactive                                               
info    print job info                                                           
list    list info for multiple jobs                                              
reset   reset job, process again                                                 
======= =========================================================================


settings
========
View and edit local settings for this anonapi instance. Credentials that are used to communicate with the API. See
:ref:`configure_credentials`.

============ ====================================================================
Command      Description                                                         
============ ====================================================================
get-token    Obtain a security token                                             
info         show current credentials                                            
set-username Set the given username in settings                                  
============ ====================================================================

Settings are stored in the users home directory in a file called `AnonWebAPIClientSettings.yml`

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
             id  date                 status      down    proc  user
          -----  -------------------  --------  ------  ------  -------
          1      2016-08-26T15:04:44  INACTIVE  0          0    z123456
          2      2016-08-26T15:04:44  ERROR     503        100  z123456
          3      2016-08-26T15:04:44  DONE      1155       1155 z123456

batch command overview:

=========== =====================================================================
Command     Description                                                          
=========== =====================================================================
add         Add ids to current batch. Space-separated (1 2 3) or range (1-40)    
cancel      Cancel every job in the current batch                                
delete      delete batch in current folder                                       
info        Show batch in current directory                                      
init        Save an empty batch in the current folder, for current server        
remove      Remove ids from current batch. Space-separated (1 2 3) or range (1-40
reset       Reset every job in the current batch                                 
reset-error Reset all jobs with error status in the current batch                
show-error  Show full error message for all error jobs in batch                  
status      Print status overview for all jobs in batch                          
=========== =====================================================================


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

.. _batch_status:

status
------
Show a table with status for all jobs in the batch in current directory.

.. code-block:: console

    $ anon batch status  # Now you can print status for all ids in this batch
    > Job info for 3 jobs on p01:
         id  date                 status      down    proc  user
      -----  -------------------  --------  ------  ------  -------
      1      2016-08-26T15:04:44  INACTIVE  0          0    z123456
      2      2016-08-26T15:04:44  ERROR     503        100  z123456
      3      2016-08-26T15:04:44  DONE      1155       1155 z123456

Modifiers:

--patient-name
    With this modifier a column `anon_name` is added, which shows the anonymized name used in this job:

    .. code-block:: console

        $ anon batch status --patient-name
        > Job info for 3 jobs on p01: https://umcradanonp11.umcn.nl/p01:
             id  date                 status      down    proc  user     anon_name
          -----  -------------------  --------  ------  ------  -------  ---------
          1      2016-08-26T15:04:44  INACTIVE  0          0    z123456  patient34
          2      2016-08-26T15:04:44  ERROR     503        100  z123456  patient40
          3      2016-08-26T15:04:44  DONE      1155       1155 z123456  patient41


.. _map:

map
===
Create a mapping between data and anonymization parameters. This mapping contains everything needed to create
anonymization jobs

Overview of map functions:

===================== ===========================================================
Command               Description                                                
===================== ===========================================================
add-all-study-folders Add all folders matching pattern to mapping                
add-selection         Add selection file to mapping                              
add-study-folder      Add all dicom files in given folder to map                 
delete                delete mapping in current folder                           
edit                  Edit the current mapping in OS default editor              
init                  Save a default mapping in the current folder               
status                Show mapping in current directory                          
===================== ===========================================================

.. _map_add_study_folder:

add-study-folder
----------------

Add the given folder to :ref:`mapping <concepts_mapping>`. This is done by finding all dicom files in the folder and any folders below it, adding
those to a :ref:`file selection <concepts_selection>`, and then adding the file selection to the mapping.

Options:

--check-dicom/ --no-check-dicom
	Open each file to check whether it is valid DICOM. Turning this off is faster, but the anonymization fails if non-DICOM files are included. On by default

Example:

.. code-block:: console

    $ anon map add-study-folder folder1/
    > Adding 'folder1' to mapping
    > Finding all files in folder1
    > 1it [12:01, 145.41it/s]
    > Found 1512 files. Finding out which ones are DICOM
    > 100%|██████████████████████████████████████████████| 1420/1512 [00:00<00:00, 10.51it/s]
    > Found 1420 DICOM files


To find out which files are DICOM, each file is opened as DICOM. If this succeeds the file is added. This makes
sure that only valid DICOM is sent to the anonymization server.

Running the command ``anon map add-study-folder <folder>`` is equivalent to running ``anon select add <folder>`` and then
``anon map add-selection-file <folder>/fileselection.txt``


.. note::

    For folders with many files, add-study-folder might take several seconds up to a minute to complete.


add-all-study-folders
---------------------

Runs :ref:`add-study-folder <map_add_study_folder>` on all folders that match pattern. The pattern can include ``*``
to match part of a file or folder and ``**`` to match any combination of folders and filenames.

Options:

--check-dicom/ --no-check-dicom
	Open each file to check whether it is valid DICOM. Turning this off is faster, but the anonymization fails if non-DICOM files are included. On by default

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
    |   |   |--test.dcm
    |   |   |--othertest.dcm
    |   |   |--raw
    |   |       |--test2.dcm
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

    # tip: On linux bash terminals, the pattern needs to be
    #      quoted to avoid automatic expansion

.. note::

    Make sure that each added path contains data for only one patient. You can only map one patient name and id
    to each path.


.. _map_add_selection_file:

add-selection-file
------------------

Add the given :ref:`file selection <concepts_selection>` file to :ref:`mapping <concepts_mapping>`. This will create
a new row in the mapping

.. _map_edit:

edit
----
Open the :ref:`mapping <concepts_mapping>` file in current dir in the default editor for csv files. On windows this is usually excel.

.. warning::

    Always close the editor before running anon commands that modify the mapping like :ref:`map_add_selection_file`.
    Many editors lock the file while open, making it impossible to change it by other means.

Some editors will ask you whether you want to save the mapping file in their own file format like xlsx. Never do this as
this will make the mapping unreadable for anonapi.


.. _map_init:

init
----
Create a :ref:`mapping <concepts_mapping>` in the current folder containing some default content. `destination_path` and
`project` are based on the defaults set with the :ref:`create set-defaults <create>` command

.. _select:

select
======
select files for a single anonymization job. The selection is saved in a :ref:`file selection <concepts_selection>` file.

Overview of select functions:

======= =========================================================================
Command Description                                                              
======= =========================================================================
add     Add all files matching pattern to selection in the current directory.Excl
delete  Remove selection file in current directory                               
edit    Open selection file in default editor                                    
status  Show selection in current directory                                      
======= =========================================================================

.. _select_add:

add
---
Add all files matching pattern paths to a :ref:`file selection <concepts_selection>` in the current folder. Pattern can use
``*`` to match any part of a name. Excludes files called `fileselection.txt`

There are several modifiers available:

--recurse/ --no-recurse
	Search for files to add in subfolders as well. On by default

--check-dicom/ --no-check-dicom
	Only add files that are valid DICOM file. For many files, this might take some time. Off by default.

--exclude-pattern, -e
	Exclude any file matching the given pattern. The pattern can use ``*`` to match any part of a name. --exclude-pattern can be used multiple times, to exclude multiple patterns

Examples of different selections. Given the following folder structure::

        patient1
        |--study1
        |   |--file1.dcm             (valid DICOM file)
        |   |--bigfile.raw           (valid DICOM file)
        |--study2
        |   |-123.1224.5354.543.4    (valid DICOM file)
        |   |-123.1224.2534.34.2     (valid DICOM file)
        |--fileselection.txt
        |--screenshots
        |   |--shot1.jpg


You can select files like this:

.. code-block:: console

    $ anon select add *                 # adds all files in the folder except 'fileselection.txt'
    $ anon select add --check-dicom *   # adds both files in study1 and both in study2
    $ anon select add study2/*          # adds both files in study2
    $ anon select add *.dcm             # adds only study1/file1.dcm

    $ anon select add * --exclude-pattern *.raw  # all DICOM except study1/bigfile.raw

    $ anon select add * --exclude-pattern *.raw --exclude-pattern *.dcm  # only files in study2


.. _create:

create
======
create jobs on server

Overview of create functions:

============= ===================================================================
Command       Description                                                        
============= ===================================================================
from-mapping  Create jobs from mapping in current folder                         
set-defaults  Set project name used when creating jobs                           
show-defaults show project name used when creating jobs                          
============= ===================================================================

.. _create_from_mapping:

from-mapping
------------
Create a job for each row in the :ref:`concepts_mapping` in the current directory. This will do some validation and ask
for confirmation:

.. code-block:: console

    $ anon create from-mapping
    > This will create 3 jobs on p01, for projects '['Wetenschap-Algemeen']',
    > writing data to '['\\\\server\\share\\folder']'. Are you sure? [y/N]:
    $ Y
    > Created job with id 1
    > Created job with id 2
    > Created job with id 3
    > created 3 jobs: [1, 2, 3]
    > Saving job ids in batch in current folder
    > Done

The command will create a :ref:`concepts_batch` in the current folder containing each created job. This means you can
use all :ref:`batch` commands on your created jobs:

.. code-block:: console

    $ anon batch info
    > job_ids:
    > - '1'
    > - '2'
    > - '3'
    > server:
    >   name: p01
    >   url: https://anonserver_p01/api