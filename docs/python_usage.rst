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

A more extended python example of creating, modifying and cancelling jobs can be found in the in
:ref:`examples`.
