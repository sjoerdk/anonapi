#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for the `anonapi.client` module."""
import json

import pytest
from _pytest.fixtures import fixture

from anonapi.client import WebAPIClient, APIClientAPIException
from tests.factories import RequestsMock, RequestsMockResponseExamples


@fixture
def mocked_requests_client():
    """A WebAPIClient instance that does not actually do http calls but uses mocked responses

    Returns
    -------
    (WebAPIClient, RequestsMock)
        client with mocked requests lib, and te mocked requests lib itself

    """
    client = WebAPIClient(hostname='test.host', username='testuser', token='token')

    requests_mock = RequestsMock()
    client.requestslib = requests_mock
    return client, requests_mock


def test_basic_client(mocked_requests_client: WebAPIClient):
    """Request documentation from server"""
    client, requests_mock = mocked_requests_client

    requests_mock.set_response(text=json.dumps({"documentation": 'some docs'}))
    assert client.get_documentation() == 'some docs'


def test_get_jobs(mocked_requests_client: WebAPIClient):
    """Get info on last jobs from server"""
    client, requests_mock = mocked_requests_client

    # job list with two jobs.
    requests_mock.set_response(text=RequestsMockResponseExamples.JOBS_LIST)
    response = client.get("get_jobs")
    assert len(response) == 2


def test_get_job(mocked_requests_client: WebAPIClient):
    """Get info on a single job """
    client, requests_mock = mocked_requests_client

    # job info for a job with id=3
    requests_mock.set_response(text=RequestsMockResponseExamples.JOB_INFO)
    response = client.get("get_job", job_id=3)
    assert response['job_id'] == 3
    assert response['user_name'] == 'z123sandbox'


def test_modify_job(mocked_requests_client: WebAPIClient):
    """Get info on a single job """
    client, requests_mock = mocked_requests_client

    # modify status. For a real server this would return the modified job. For test just return test job
    requests_mock.set_response(text=RequestsMockResponseExamples.JOB_INFO)
    _ = client.post('modify_job', job_id=3, status="INACTIVE")
    assert requests_mock.requests.post.called


def test_wrong_inputs(mocked_requests_client: WebAPIClient):
    """Make some impossible requests of the server"""
    client, requests_mock = mocked_requests_client
    requests_mock: RequestsMock

    # getting non-existent job, Server will respond with
    requests_mock.set_response(text=RequestsMockResponseExamples.JOB_DOES_NOT_EXIST, status_code=400)
    with pytest.raises(APIClientAPIException) as exception:
        client.get('get_job', job_id=100)
    assert 'does not exist' in str(exception.value)

    # passing insufficient parameters
    requests_mock.set_response(text=RequestsMockResponseExamples.REQUIRED_PARAMETER_NOT_SUPPLIED, status_code=400)
    with pytest.raises(APIClientAPIException) as exception:
        client.get('get_job')
    assert 'Required parameter' in str(exception.value)

    # passing insufficient parameters
    requests_mock.set_response(text=RequestsMockResponseExamples.API_CALL_NOT_DEFINED, status_code=400)
    with pytest.raises(APIClientAPIException) as exception:
        client.get('sgetdf_jfob')
    assert 'The API call you tried to make is not defined' in str(exception.value)









