.. _command_reference:

=================
Command reference
=================

Information on specific anonapi CLI functions. For more general information on how to achieve specific goals, see :doc:`usage`


.. note::
    Detailed help on commands is often available directly from the command line by adding ``--help`` to any command. See :ref:`getting_info_on_commands`

======
status
======

Display information on the command line tool itself. Which API servers it knows about, current active server


.. _server_commands:

======
server
======
Work with Anonymization server API servers. Add, remove servers, set active server

Overview of server functions:

======== ========================================================================
Command  Description                                                             
======== ========================================================================
activate Set given server as activate server, meaning subsequent operations will 
add      Add a server to the list of servers in settings                         
jobs     List latest 100 jobs for active server, or given server                 
list     show all servers in settings                                            
remove   Remove a server from list in settings                                   
status   Check whether active server is online and responding like an anonymizati
======== ========================================================================


===
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

========
settings
========
Local settings for this anonapi instance. Credentials that are used to communicate with the API.


.. _batch:

=====
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

=========== =====================================================================
Command     Description                                                          
=========== =====================================================================
add         Add ids to current batch. Will not add already existing. Space separa
cancel      Cancel every job in the current batch                                
delete      delete batch in current folder                                       
info        Show batch in current directory                                      
init        Save an empty batch in the current folder, for current server        
remove      Remove ids from current batch. Space separated, ranges like 1-40 allo
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


.. _map:

===
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


.. _select:


======
select
======
select files for a single anonymization job


Overview of select functions:

======= =========================================================================
Command Description                                                              
======= =========================================================================
add     Add all files matching given pattern to the selection in the current fold
delete  Show selection in current directory                                      
edit    initialise a selection for the current directory, add all DICOM files    
status  Show selection in current directory                                      
======= =========================================================================


.. _create:


======
create
======
create jobs


Overview of create functions:

============= ===================================================================
Command       Description                                                        
============= ===================================================================
from-mapping  Create jobs from mapping in current folder                         
set-defaults  Set project name used when creating jobs                           
show-defaults show project name used when creating jobs                          
============= ===================================================================