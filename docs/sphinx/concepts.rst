.. _concepts:

========
Concepts
========

The idea behind certain objects used in anonapi

.. _concepts_batch:

Batch
=====

A file holding one or more job ids. This makes it possible to easily query or modify several jobs at once. See :ref:`batch`

.. _concepts_mapping:

Mapping
=======

A file that contains everything that is needed to create one or more anonymization jobs. See :ref:`map`

A typical mapping file will look like this::

    ## Description ##
    Mapping created February 12 2020

    ## Options ##
    root_source_path, \\server\share2\data
    project,          Wetenschap-Algemeen
    destination_path, \\server\share\folder

    ## Mapping ##
    source,                           patient_id, patient_name, description
    folder:example/folder1,           001,        Patient1,     All files from folder1
    study_instance_uid:123.12178,     002,        Patient2,     A StudyInstanceUID from PACS
    accession_number:12345678.1234567,003,        Patient3,     An AccessionNumber from PACS
    fileselection:a/fileselection.txt,004,        Patient4,     A selection of files in a

Available parameters:

* source

* patient_id

* patient_name

* description

* pims_key

* destination_path

* root_source_path

* project

.. _concepts_job:

Job
===

The basic unit of information on an anonymization server. A job specifies three things.
Where the data is, how to anonymize it and where it should go. See :ref:`job`

.. _concepts_selection:

File Selection
==============

A file typically called ``fileselection.txt`` that contains a list of paths. A selection can be a data source for a job.
It makes it possible to exactly define which files should be sent for anonymization and which should not. Methods like
:ref:`add-study-folder <map_add_study_folder>` and :ref:`select_add` will only include valid DICOM files in a selection.

The contents of a typical file selection::

    description: a typical file selection
    id: bfc33f5e-d1cc-472e-aa05-31a5979d52be
    selected_paths:
    - folder1/1.dcm
    - folder1/2.dcm
    - folder2/1.dcm
    - folder4/raw/raw1.dcm

A selection file can be edited by any text editor. See :ref:`select`

.. note::

    Selected paths are always relative to the location of ``fileselection.txt``. Selected paths are always in a path on or below the selection file.



.. _concepts_server:

Server
======
An anonymization server fetches, anonymizes and delivers your data according to the jobs it gets.