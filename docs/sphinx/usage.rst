.. _usage:

=====
Usage
=====

Information on how to achieve certain goals using anonapi. For detailed information on specific commands, see :doc:`command_reference`

.. _usage_starting_a_command_prompt:

Starting a command prompt
=========================
After :doc:`installation` and :doc:`configuration` you can use the CLI from a command prompt. The way to do this varies
between windows and linux:

Windows
    Press the start menu and type ``cmd`` and press enter. For more info see
    see `here <https://www.lifewire.com/how-to-open-command-prompt-2618089>`_. Certain anonapi commands, such as
    :ref:`batch`, work in specific folders. To open command prompt in a specific folder in windows see `here
    <https://helpdeskgeek.com/how-to/open-command-prompt-folder-windows-explorer/>`_

Linux
    This varies between distributions. Common ways are pressing Meta+t, ``Konsole`` on ubuntu, or ``Terminal``. For more info see
    `here <https://www.howtogeek.com/140679/beginner-geek-how-to-start-using-the-linux-terminal/>`_

.. _getting_info_on_commands:

Getting info on commands
========================
All CLI commands have the following form:

.. code-block:: console

    $ anon <command-group> <command> <arguments>   # General form
    $ anon job info 1234                           # Example: get info for job '1234'
    $ anon server activate server2                 # Example: Activate the server named 'server2'

A list of commands for any command group can be printed this way:

.. code-block:: console

    $ anon job                # Shows all commands for command group 'job'
    $ anon settings           # Shows all commands for command group 'settings'
    $ anon <command-group>    # General form. Shows all commands for any command group

Detailed help on commands is often available directly from the command line by adding ``--help`` to any command. For example:

.. code-block:: console

    $ anon job info --help                         # Shows detailed help for job info
    $ anon server activate --help                  # Shows detailed help for server activate



.. _information_about_jobs:

Information about jobs
======================

.. code-block:: console

    $ anon server jobs    # shows last 100 jobs on server
    $ anon job info 123   # shows details for job with id 123

.. tip:: see :ref:`job_status_codes` for more information on job status


.. _cancel_or_restart_jobs:

Cancel or restart jobs
======================

.. code-block:: console

    $ anon job reset 123   # reset job with id 123
    $ anon job cancel 123  # cancel job with id 123


Multiple jobs at once (batch)
=============================

More information on job batches: :ref:`batch`

.. code-block:: console

    $ cd C:/myfolder            # any folder you want. One folder can only contain one batch.
    $ anon batch init           # initialises an empty batch
    $ anon batch add 10 11 13   # add three job ids to this batch
    $ anon batch add 20-35      # add fifteen job ids: 20 through to 35
    $ anon batch status         # print info for all jobs in batch
    $ anon batch                # see other commands including reset and cancel all


Creating jobs
=============

The general procedure for creating a jobs is as follows:

#. :ref:`open a terminal<usage_starting_a_command_prompt>`
#. create a :ref:`mapping <concepts_mapping>` using the :ref:`map init<map_init>` command
#. edit the mapping to suit your needs. Most commands for this are in the :ref:`map` command group
#. based on the mapping, run the :ref:`create from-mapping <create_from_mapping>` command
#. monitor your jobs progress with the :ref:`batch status <batch>` command

Two specific cases are shown below

.. _anonymize_files_from_pacs:

Anonymize files from PACS
=========================
For this example we want to retrieve and anonymize the following studies from PACS:

* A study with AccessionNumber 123456.1234567
* A study with AccessionNumber 123456.2234568
* A study with StudyInstanceUID 123.1232.23.24

To do this, follow these steps:

.. code-block:: console

    $ anon map init
    > Initialised example mapping in anon_mapping.csv

    $ anon map edit    # opens mapping for editing

Now edit the mapping until it looks like this:

.. code-block:: text

    ## Description ##
    Mapping created February 12 2020

    ## Options ##
    project,          Wetenschap-Algemeen
    destination_path, \\server\share\myoutput

    ## Mapping ##
    source,                            patient_id, patient_name, description
    accession_number:123456.1234567,   001,        Patient2,     Test PACS project
    accession_number:123456.2234568,   002,        Patient2,     Test PACS project
    study_instance_uid:123.1232.23.24, 003,        Patient3,     Test PACS project

Now close the editor and do:

.. code-block:: console

    $ anon create from-mapping
    > This will create 3 jobs on p01, for projects '['Wetenschap-Algemeen']' etc..
    > Done

To monitor the status of your created jobs, use:

.. code-block:: console

    $ anon batch status



.. _anonymize_files_from_share:

Anonymize files from a share
============================

