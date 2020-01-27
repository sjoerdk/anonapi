============
Python Usage
============

How to use anonapi from within a python script

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

Examples
========

These examples are taken from the code in the :ref:`examples` directory


Anonymize from IDC
------------------
IDC is the hospital medical image server

.. literalinclude:: ../examples/anonymize_files_from_idc.py


Anonymize from network share
----------------------------

.. literalinclude:: ../examples/anonymize_files_from_share.py


Filter on SOPClass
------------------
SOPClassUID is the DICOM 'image type'

.. literalinclude:: ../examples/anonymize_files_sop_class_filter.py


Cancel job
----------

.. literalinclude:: ../examples/cancel_job.py


Get job status
--------------

.. literalinclude:: ../examples/get_job_status.py


Modify jobs
-----------

.. literalinclude:: ../examples/modify_jobs.py
