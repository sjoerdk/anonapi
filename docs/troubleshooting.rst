===============
Troubleshooting
===============

Examples of commonly encountered errors when using the anonymization api CLI


.. _common_anonapi_errors:

Common anonapi errors
=====================

Error Max retries exceeded
--------------------------
When getting information from server, something like this

.. code-block:: JavaScript

  Error getting jobs from p01: https://umcradanonp11.umcn.nl/p01:
  HTTPSConnectionPool(host='umcradanonp11.umcn.nl', port=443): Max retries exceeded
  with url: /p01/get_jobs (Caused by NewConnectionError('<urllib3.connection.
  VerifiedHTTPSConnection object at 0x7f5580875198>: Failed to establish a
  new connection: [Errno 111] Connection refused'))


This means the anonymization api server is not responding. Check the end of the message.If it says 'Connection refused',
the server is online but not responding. Inform a server admin.

If it says 'Name or service not known', the url you have entered for the server might be wrong. Recheck :ref:`add_a_server_to_CLI`


Unexpected response code 500
----------------------------
Something like

.. code-block:: JavaScript

  Error getting job info from t01: https://umcradanonp11.umcn.nl/t01:
  Unexpected response from WebAPIClient for z428172@https://umcradanonp11.umcn.nl/t01:
  code '500', reason 'Internal Server Error'

There is something wrong with the job itself. Inform a server admin.


.. _common_job_errors:

Common job errors
=================
Error messages you might encounter when getting :ref:`information_about_jobs`


.. _job_stuck_on_UPLOADED:

Job stuck on status UPLOADED
----------------------------

Example

.. code-block:: JavaScript

    job 50881 on t01:

    ('job_id', 50881)
    ('date', '2019-04-29T12:13:55')
    ('user_name', 'z123456')
    ('status', 'UPLOADED')                  <==  Status does not change
    ('error', None)                         <==  No error message
    ('description', 'Ultrasound test')
    ('project_name', 'Wetenschap-Algemeen')
    ('priority', 30)
    ('files_downloaded', 1683)
    ('files_processed', 1600)               <== Not all downloaded files have been processed

Stuck on UPLOADED usually means that part or all of the collected data is being quarantined. This regularly happens with
data with burned in annotations such as ultrasound. The system will have to be explicitly shown which portions of images
contain patient information.

Solution: record job id and send to anonapi admin

HTTP 404 not found
------------------

Example

.. code-block:: JavaScript

    job 52019 on p03:

    ('job_id', 112323)
    ('date', '2019-06-14T12:14:04')
    ('user_name', 'z123456')
    ('status', 'ERROR')
    ('error', "Error while pre-processing job 52019: WadoWrapperException: Got HTTP error response
               from server when requesting 'http://umcidcsasp04:8080/wado/?studyInstanceUID=1234
               &contentType=application/dicom&requestType=WADO&transferSyntax=1.2.840.10008.1.2.1'
               Original error:'HTTP Error 404: Not Found'")
    ('description', Test)
    ('project_name', 'Wetenschap-Algemeen')

This often means data could not be retrieved from the hospital image server. This might be due to a temporary glitch in that server.

Solution: retry job after at least 30 minutes. See :ref:`cancel_or_restart_jobs`

HTTP 400 server error
---------------------
Example

.. code-block:: JavaScript

    job 52863 on p03:

    ('job_id', 12345)
    ('date', '2019-07-22T10:46:48')
    ('user_name', 'Z123456')
    ('status', 'ERROR')
    ('error', "Error while pre-processing job 52863: WadoWrapperException: Got HTTP error response"
              "from server when requesting 'http://umcidcsasp04:8080/wado/?studyInstanceUID=1234"
              "&contentType=application/dicom&requestType=WADO&transferSyntax=1.2.840.10008.1.2.1'"
              "Original error:'HTTP Error 400: Bad Request'")
    ('description', A test project)
    ('project_name', 'Wetenschap-Algemeen')


The end of the error message is important. There was an internal error in the hospital image server when retrieving the
data for this job. This sometimes happens for incorrectly imported data or additional findings that have been
incorrectly pushed to the images server.

Solution: Record the accession number for the data in this job and ask beeld en zorg to check for errors in that data.

Could not move file
-------------------

Example

.. code-block:: JavaScript

    job 52132 on p03:

    ('job_id', 52132)
    ('date', '2019-06-14T12:14:12')
    ('user_name', 'z1234567')
    ('status', 'ERROR')
    ('error', 'Could not move file D:\\CTP\\roots\\Post-anonimizationDSS\\52132\\test\\'
               'to \\\\umcsanfsclp01\\radng_trialbureau\\52132\\test\\,'
               'original error:[Errno 28] No space left on device')
    ('description', None)
    ('project_name', 'Wetenschap-Algemeen')

The share that the data is going to is full. Make sure there is enough space and retry

Patient has opted out
---------------------

Example

.. code-block:: JavaScript

    job 51815 on p03:

    ('job_id', 51815)
    ('date', '2019-06-14T12:13:49')
    ('user_name', 'z123456')
    ('status', 'ERROR')
    ('error', 'Error while pre-processing job 51815: Patient "123456" does not want'
               'his or her data to be used for research')
    ('description', None)
    ('project_name', 'Wetenschap-Algemeen')

The patient associated with this data has indicated he or she does not want his or her data to be used for research
purposes. You cannot use this data. If the patient has signed a specific declaration of consent for your specific
research, contact the trial bureau.


.. _job_status_codes:

Job status codes
================
These are part of the info you get when getting :ref:`information_about_jobs`. For example

.. code-block:: JavaScript

    job 51815 on p03:

    ('job_id', 51815)
    ('date', '2019-06-14T12:13:49')
    ('user_name', 'z123456')
    ('status', 'DONE')      <== that one

Job status codes and their meaning:

ACTIVE
    This job is waiting to be processed by the server
UPLOADED
    Uploaded to anonymization core. If a job has this status for longer than 30 minutes, refer to :ref:`job_stuck_on_UPLOADED`
DONE
    Data has been processed and copied to final destination. Some quarantined files such as embedded pdfs might still be held back.
ERROR
    Something went wrong. Refer to :ref:`common_job_errors` for more information.
