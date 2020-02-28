.. _python_usage:

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

Testing
=======
The :mod:`anonapi.testresources` module can be used to generate mock responses without the need for a live server:

.. code-block:: python

    from anonapi.testresources import (
        MockAnonClientTool,
        JobInfoFactory,
        RemoteAnonServerFactory,
        JobStatus,
    )

    # Create a mock client tool that returns information about jobs
    tool = MockAnonClientTool()

    # Client tool methods need a server to query. This is mocked too here
    mock_server = RemoteAnonServerFactory()
    tool.get_job_info(server=mock_server, job_id=1)    # Returns realistic JobInfo response

    # You can set the responses that mock client cycles through:
    some_responses = [
        JobInfoFactory(status=JobStatus.DONE),
        JobInfoFactory(status=JobStatus.ERROR),
        JobInfoFactory(status=JobStatus.INACTIVE),
    ]
    tool = MockAnonClientTool(responses=some_responses)
    tool.get_job_info(mock_server, job_id=1).status # returns JobStatus.DONE
    tool.get_job_info(mock_server, job_id=1).status # returns JobStatus.ERROR
    tool.get_job_info(mock_server, job_id=1).status # returns JobStatus.INACTIVE
    tool.get_job_info(mock_server, job_id=1).status # returns JobStatus.DONE again

    # You can set any of the JobInfo fields on the JobInfo instances:
    JobInfoFactory(project_name='project1',
                   destination_path='\\server\share\folder',
                   priority=50)


Exceptions
==========
All exceptions raised in anonapi derive from :mod:`anonapi.exceptions.AnonAPIException`. Catching that will allow you to
handle them:

.. code-block:: python

    from anonapi.exceptions import AnonAPIException
    from anonapi.client import AnonClientTool

    tool = AnonClientTool('user','token')
    server = RemoveAnonServer('a_server','https://aserver')
    try:
        tool.get_server_status(server)

    except AnonAPIException as e:
        print(f"Something went wrong but its anonapi's fault. Look: {e}")



Examples
========

These examples are taken from the code in the :ref:`examples` directory


Anonymize from IDC
------------------
IDC is the hospital medical image server

.. literalinclude:: ../../examples/anonymize_files_from_idc.py


Anonymize from network share
----------------------------

.. literalinclude:: ../../examples/anonymize_files_from_share.py


Filter on SOPClass
------------------
SOPClassUID is the DICOM 'image type'

.. literalinclude:: ../../examples/anonymize_files_sop_class_filter.py


Cancel job
----------

.. literalinclude:: ../../examples/cancel_job.py


Get job status
--------------

.. literalinclude:: ../../examples/get_job_status.py


Modify jobs
-----------

.. literalinclude:: ../../examples/modify_jobs.py
