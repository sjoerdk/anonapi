#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for the `anonapi.client` module."""
import json

from _pytest.fixtures import fixture

from anonapi.client import WebAPIClient
from tests.factories import RequestsMock


@fixture
def mocked_requests_client():
    """A WebAPIClient instance that does not actually do http calls but uses mocked responses

    Returns
    -------
    WebAPIClient
        client with mocked requests lib, available through the .requestslib field

    """
    client = WebAPIClient(hostname='test.host', username='testuser', token='token')
    client.requestslib = RequestsMock()
    return client


def test_basic_client(mocked_requests_client: WebAPIClient):
    mocked_requests_client.requestslib: RequestsMock
    mocked_requests_client.requestslib.set_response(text=json.dumps({"documentation": 'some docs'}))
    mocked_requests_client.get_documentation()
