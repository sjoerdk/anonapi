.. _usage:

=====
Usage
=====

Starting a command prompt
=========================
After :doc:`installation` and :doc:`configuration` you can use the CLI from a command prompt by typing

.. code-block:: console

    $ anon


For information on how to open a command prompt on windows,
see `How to open a command prompt <https://www.lifewire.com/how-to-open-command-prompt-2618089>`_.

Certain anonapi commands, such as :ref:`batch`, work in specific folders. To `open command prompt in a specific folder in windows, see here
<https://helpdeskgeek.com/how-to/open-command-prompt-folder-windows-explorer/>`_


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
