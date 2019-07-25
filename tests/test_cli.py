#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest

from click.testing import CliRunner

from anonapi.cli import AnonClientTool, AnonCommandLineParser
from anonapi.objects import RemoteAnonServer
from anonapi.settings import AnonClientSettings
from tests.factories import RequestsMock, RequestsMockResponseExamples


@pytest.fixture
def anonapi_mock_cli():
    """Returns AnonCommandLineParser object

    """
    settings = AnonClientSettings(
        servers=[RemoteAnonServer(name="testserver", url="https://testurl")],
        user_name="testuser",
        user_token="testtoken",
    )
    tool = AnonClientTool(username=settings.user_name, token=settings.user_token)
    return AnonCommandLineParser(client_tool=tool, settings=settings)


@pytest.fixture
def mock_requests(monkeypatch):
    """Replace requests lib with a mock version that does not hit any server and can return arbitrary responses

    """
    requests_mock = RequestsMock()
    monkeypatch.setattr("anonapi.client.requests", requests_mock)
    return requests_mock


def test_command_line_tool_basic(anonapi_mock_cli):
    """Test most basic invocation"""

    runner = CliRunner()
    result = runner.invoke(anonapi_mock_cli.main)
    assert result.exit_code == 0
    assert "anonymization web API tool" in result.stdout


def test_command_line_tool_status_without_active_server(anonapi_mock_cli):
    """Error found live, making sure its fixed """
    anonapi_mock_cli.settings.active_server = None
    runner = CliRunner()

    # this should not crash
    result = runner.invoke(anonapi_mock_cli.main, ["status"])

    assert result.exit_code == 0
    assert "Available servers" in result.stdout


def test_command_line_tool_add_remove_server(anonapi_mock_cli):
    """Test commands to add, remove servers and see whether the number servers that are known is correct"""

    runner = CliRunner()
    assert len(anonapi_mock_cli.settings.servers) == 1
    runner.invoke(
        anonapi_mock_cli.main, ["server", "add", "a_server", "https://test.com"]
    )

    assert len(anonapi_mock_cli.settings.servers) == 2
    result = runner.invoke(anonapi_mock_cli.main, ["server", "remove", "testserver"])

    assert len(anonapi_mock_cli.settings.servers) == 1

    # removing a non-existent server should not crash but yield nice message
    result = runner.invoke(
        anonapi_mock_cli.main, ["server", "remove", "non_existant_server"]
    )
    assert result.exit_code == 2
    assert "invalid choice" in str(result.output)


def test_command_line_tool_server_status(anonapi_mock_cli, mock_requests):
    """Test checking status"""

    runner = CliRunner()

    # basic check. Call a server that responds with an expected anonapi json response
    # API_CALL_NOT_DEFINED is a response that is used to check the liveness of a server currently.
    mock_requests.set_response(RequestsMockResponseExamples.API_CALL_NOT_DEFINED)
    result = runner.invoke(anonapi_mock_cli.main, ["server", "status"])

    assert "OK" in result.output
    assert mock_requests.requests.get.call_count == 1

    # now test a non-responsive server:
    mock_requests.reset()
    mock_requests.set_response_exception(ConnectionError)
    result = runner.invoke(anonapi_mock_cli.main, ["server", "status"])

    assert "ERROR" in result.output
    assert mock_requests.requests.get.call_count == 1

    # now test a server that exists but responds weirdly:
    mock_requests.reset()
    mock_requests.set_response("Hello, welcome to an unrelated server")
    result = runner.invoke(anonapi_mock_cli.main, ["server", "status"])

    assert "is not responding properly" in result.output
    assert mock_requests.requests.get.call_count == 1


def test_command_line_tool_job_info(anonapi_mock_cli, mock_requests):
    """Test checking status"""
    runner = CliRunner()

    result = runner.invoke(anonapi_mock_cli.main, "server activate testserver".split(" "))
    assert "Set active server to" in result.output

    mock_requests.set_response(RequestsMockResponseExamples.JOB_INFO)
    result = runner.invoke(anonapi_mock_cli.main, "job info 3".split(" "))
    assert "job 3 on testserver" in result.output
    assert "'user_name', 'z123sandbox'" in result.output

