.. _concepts:

========
Concepts
========

Information on some key concepts in the anonapi CLI

.. _concepts_batch:

Batch
=====

A file holding one or more job ids. This makes it possible to easily query or modify several jobs at once. See :ref:`batch`

.. _concepts_mapping:

Mapping
=======

A file that contains everything that is needed to create one or more anonymization jobs.

A typical mapping file will look like this:

.. code-block:: text

    ## Description ##
    Mapping created February 12 2020

    ## Options ##
    root_source_path, \\server\share2\data
    project,          Wetenschap-Algemeen
    destination_path, \\server\share\folder

    ## Mapping ##
    source,                            patient_id, patient_name, description
    folder:example/folder1,            001,        Patient1,     All files from folder1
    study_instance_uid:123.12178,      002,        Patient2,     A StudyInstanceUID from PACS
    accession_number:12345678.1234567, 003,        Patient3,     An AccessionNumber from PACS
    fileselection:a/fileselection.txt, 004,        Patient4,     A selection of files in a


This is a CSV (comma separated values) file that can be edited by any editor. The most convenient way to edit is probably
the :ref:`map_edit` command.

A mapping consists of three sections:

Description
    This can contain any text. A description of what this mapping is for

Options
    Parameters that are the same for each job. The following parameters can be set:

    ================ ================================================================
    Parameter        Description                                                     
    ================ ================================================================
    destination_path Write data to this UNC path after anonymization                 
    pims_key         Use this PIMS project to pseudonymize                           
    project          Anonymize according to this project                             
    root_source_path Path sources are all relative to this UNC path                  
    ================ ================================================================

    .. note::

        Any paths defined in this section have to be :ref:`UNC paths <concepts_unc_paths>`. No windows drive letters
        like ``H:\`` or linux mounts such as ``/mnt/data`` allowed

Mapping
    Parameters that are different for each job. The following parameters can be set:

    ============ ====================================================================
    Parameter    Description                                                         
    ============ ====================================================================
    description  Job description, free text                                          
    patient_id   Patient ID to set in anonymized data                                
    patient_name Patient Name to set in anonymized data                              
    source       Data to anonymize comes from this source                            
    ============ ====================================================================

    The value of the `source` parameter is a :ref:`source identifier <concepts_source_identifier>`. The different types of identifiers are
    listed below.

For an overview of map functions, see :ref:`map`.

.. _concepts_source_identifier:

Source Identifier
==================
Used in :ref:`mapping <concepts_mapping>` to indicate where the data for a job is coming from. Always of the form
``<identifier_type>:<value>``. Types of identifiers:

Folder
    Example: ``folder:mydata/experiment1``

    Refers to all files in the given folder, relative to the source root path.

.. note::

    If the folder contains any files that are not valid DICOM, the job will fail. Only use this identifier if you
    want to anonymize all files in a folder, and the folder contains only valid DICOM

File selection
    Example: ``fileselection:mydata/patient1/fileselection.txt``

    Refers to all the paths listed in the :ref:`fileselection file<concepts_selection>`. Contrary to the Folder identifier, file selection can be
    used in a folder where there are non-DICOM files or where only part of the files should be anonymized.
    When creating a fileselection with :ref:`map_add_study_folder` or :ref:`select_add`, non-DICOM files can be excluded
    automatically

Study instance UID
    Example: ``study_instance_uid:123.1217.23234.2323``

    Refers to a single study. The anonymization server will retrieve this study from PACS by matching the DICOM tag StudyInstanceUID.

Accession number
    Example: ``accession_number:12345678.1234567``

    Refers to a single study. The anonymization server will retrieve this study from PACS by matching the DICOM tag AccessionNumber.


.. _concepts_job:

Job
===

The basic unit of information on an anonymization server. A job specifies three things.
Where the data is, how to anonymize it and where it should go. For working with jobs see :ref:`job`.

.. _concepts_selection:

File Selection
==============

A file typically called ``fileselection.txt`` that contains a list of paths. A selection can be a data source for a job.
It makes it possible to exactly define which files should be sent for anonymization and which should not. Methods like
:ref:`add-study-folder <map_add_study_folder>` and :ref:`select_add` will only include valid DICOM files in a selection.

The contents of a typical file selection that contains 4 file paths::

    description: a typical file selection
    id: bfc33f5e-d1cc-472e-aa05-31a5979d52be
    selected_paths:
    - folder1/1.dcm
    - folder1/2.dcm
    - folder2/1.dcm
    - folder4/raw/raw1.dcm

A selection file can be edited by any text editor. See :ref:`select`.

.. note::

    Selected paths are always relative to the location of ``fileselection.txt``. Selected paths are always in a path on or below the selection file.



.. _concepts_server:

Server
======
An anonymization server fetches, anonymizes and delivers your data according to the :ref:`jobs <concepts_job>` it has in its database.
Servers can retrieve data from PACS or from network shares. The anonapi CLI can work with multiple servers. See :ref:`server_commands`.

.. _concepts_unc_paths:

UNC paths
=========
Any path sent to the anonymization server should be a UNC path. A UNC path is any path starting with::

    \\<server_name>\<share_name>

For example::

    \\umcfilesp01\research\folder1\file.dcm
    \\server1\share2\myfolder\

UNC paths are mandatory for creating :ref:`anonymization jobs <concepts_job>` because they are well supported in most
operating systems and unambiguous. In contrast, windows drive letters such as ``C:\``, mapped network drives such as ``X:\`` and
linux mounts like ``/mnt/share1`` can refer to different locations on different computers.

You can find more `unc_path_info <https://www.lifewire.com/unc-universal-naming-convention-818230>`_ online.

.. _concepts_finding_a_unc_path:

Finding a UNC path
------------------
Windows
    In windows shares are often `mapped <https://support.microsoft.com/en-us/help/4026635/windows-map-a-network-drive>`_
    to a drive letter such as ``H:\`` or ``X:\``. To find the UNC path for these drive letters, open windows explorer (start menu -> explorer)
    and expand the computer icon in the lower left side:

    .. image:: static/screenshot.jpg
       :scale: 100 %
       :alt: Finding UNC paths in windows

    In this example ``(H:) radngdata$ (\\umcfs097)`` corresponds to the UNC path ``\\umcfs097\radngdata$`` note the path
    in this case includes the final ``$``

Linux
    In linux UNC paths are mounted in fstab. Use::

        $ less  /etc/fstab

    To find out which UNC path is mapped to which mount point.