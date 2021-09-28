#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pathlib import Path
from unittest.mock import Mock

import pytest
import requests
from click.testing import CliRunner

from anonapi.batch import JobBatch
from anonapi.cli import entrypoint
from anonapi.cli.entrypoint import get_context
from anonapi.client import APIClientException
from anonapi.context import AnonAPIContextException
from anonapi.responses import APIParseResponseException
from tests.factories import RequestsMock
from tests.mock_responses import RequestsMockResponseExamples


@pytest.fixture
def anonapi_mock_cli_with_batch(anonapi_mock_cli):
    """Returns AnonAPIContext object that has a batch defined"""

    batch = JobBatch(
        job_ids=["1000", "1002", "5000", "100000"],
        server=anonapi_mock_cli.get_active_server(),
    )
    anonapi_mock_cli.get_batch = lambda: batch  # set current batch to mock batch
    return anonapi_mock_cli


@pytest.fixture
def mock_requests(monkeypatch):
    """Replace requests lib with a mock version that does not hit any server and can
    return arbitrary responses

    """
    requests_mock = RequestsMock()
    # maintain vanilla requests errors because these need to be importable even
    # when mocking
    requests_mock.exceptions = requests.exceptions
    monkeypatch.setattr("anonapi.client.requests", requests_mock)
    return requests_mock


@pytest.fixture
def mock_anonapi_current_dir(anonapi_mock_cli, tmpdir):
    """Anonapi instance with a tempdir current dir. So you can create,
    read files in 'current dir'
    """
    anonapi_mock_cli.current_dir = str(
        tmpdir
    )  # make mock_context thinks tmpdir is its working dir
    return anonapi_mock_cli


def test_command_line_tool_basic(mock_main_runner):
    """Test most basic invocation"""

    runner = mock_main_runner
    result = runner.invoke(entrypoint.cli)
    assert result.exit_code == 0
    assert "anonymization web API tool" in result.stdout


def test_command_line_tool_status_without_active_server(mock_main_runner):
    """Error found live, making sure its fixed"""
    mock_main_runner.get_context().settings.active_server = None
    runner = CliRunner()

    # this should not crash
    result = runner.invoke(entrypoint.cli, "status", catch_exceptions=False)

    assert "Available servers" in result.stdout


def test_command_line_tool_add_remove_server(mock_main_runner):
    """Test commands to add, remove servers and see whether the number servers
    that are known is correct
    """

    runner = mock_main_runner
    context = runner.get_context()
    assert len(context.settings.servers) == 2
    runner.invoke(entrypoint.cli, "server add a_server https://test.com")

    assert len(context.settings.servers) == 3
    runner.invoke(entrypoint.cli, "server remove testserver")

    assert len(context.settings.servers) == 2

    # removing a non-existent server should not crash but yield nice message
    result = runner.invoke(entrypoint.cli, "server remove non_existant_server")
    assert result.exit_code == 2
    assert "Invalid value" in str(result.output)

    with pytest.raises(AnonAPIContextException):
        context.get_server_by_name("unknown_server")


def test_command_line_tool_list_servers(mock_main_runner):

    runner = mock_main_runner
    result = runner.invoke(entrypoint.cli, "server list", catch_exceptions=False)
    assert result.exit_code == 0
    assert all(
        [
            x in result.output
            for x in ["Available servers", "testserver ", "testserver2 "]
        ]
    )


def test_command_line_tool_server_status(mock_main_runner, mock_requests):
    """Test checking status"""

    runner = mock_main_runner

    # basic check. Call a server that responds with an expected anonapi json response
    # API_CALL_NOT_DEFINED is a response that is used to check the liveness of
    # a server currently.
    mock_requests.set_response_text(RequestsMockResponseExamples.API_CALL_NOT_DEFINED)
    result = runner.invoke(entrypoint.cli, ["server", "status"])

    assert "OK" in result.output
    assert mock_requests.requests.get.call_count == 1


def test_cli_server_status_weird_response(mock_main_runner, mock_requests):
    """If the server added is not an API server"""
    mock_requests.set_response_text("Hello, welcome to an unrelated server")
    result = mock_main_runner.invoke(
        entrypoint.cli, ["server", "status"], catch_exceptions=False
    )

    assert "is not responding properly" in result.output
    assert mock_requests.requests.get.call_count == 1


def test_cli_server_status_non_responsive_server(mock_main_runner, mock_requests):
    """Anon server status command with a server that does not respond"""

    mock_requests.reset()
    mock_requests.set_response_exception(
        requests.exceptions.ConnectionError(
            "Some long technical thing about" " max retries exceeded"
        )
    )

    result = mock_main_runner.invoke(entrypoint.cli, ["server", "status"])

    assert "cannot be reached" in result.output
    assert mock_requests.requests.get.call_count == 1


def test_server_error_responses(mock_main_runner, mock_requests):
    """Make sure request errors are correctly caught"""
    runner = mock_main_runner
    mock_requests.set_response_exception(
        requests.exceptions.ConnectionError("Maximum retries exceeded")
    )
    response = runner.invoke(entrypoint.cli, "server status", catch_exceptions=False)
    assert response.exit_code == 0


def test_command_line_tool_job_info(mock_main_runner, mock_requests):
    """Test checking status"""
    runner = mock_main_runner

    result = runner.invoke(
        entrypoint.cli, "server activate testserver", catch_exceptions=False
    )
    assert "Set active server to" in result.output

    mock_requests.set_response_text(RequestsMockResponseExamples.JOB_INFO)
    result = runner.invoke(entrypoint.cli, "job info 3", catch_exceptions=False)
    assert "job 3 on testserver" in result.output
    assert "'user_name', 'z123sandbox'" in result.output


def test_command_line_tool_job_info_multiple(mock_main_runner, mock_requests):
    """Test checking status"""
    runner = mock_main_runner

    result = runner.invoke(entrypoint.cli, "server activate testserver")
    assert "Set active server to" in result.output

    mock_requests.set_response_text(RequestsMockResponseExamples.JOB_INFO)
    result = runner.invoke(entrypoint.cli, "job info 3 2 4")
    assert "job 3 on testserver" in result.output
    assert "'user_name', 'z123sandbox'" in result.output


def test_cli_job_list(mock_main_runner, mock_requests):
    """Try operations actually calling server"""
    runner = mock_main_runner

    mock_requests.set_response_text(
        text=RequestsMockResponseExamples.JOBS_LIST_GET_JOBS_LIST
    )
    result = runner.invoke(entrypoint.cli, "job list 1000 1002 50000")
    assert all(
        text in result.output for text in ["DONE", "UPLOAD", "1000", "1002", "5000"]
    )


def test_cli_job_list_errors(mock_main_runner, mock_requests):
    """Giving no rows should yield helpful error input. Not python stacktrace"""
    runner = mock_main_runner
    mock_requests.set_response_text(
        text=RequestsMockResponseExamples.REQUIRED_PARAMETER_NOT_SUPPLIED,
        status_code=400,
    )
    result = runner.invoke(entrypoint.cli, "job list")
    assert result.exit_code == 0


def test_command_line_tool_activate_server(mock_main_runner, mock_requests):
    """Test activating a server"""

    runner = mock_main_runner
    context = mock_main_runner.get_context()
    assert context.get_active_server().name == "testserver"
    result = runner.invoke(
        entrypoint.cli, "server activate testserver2", catch_exceptions=False
    )
    assert "Set active server to" in result.output
    assert context.get_active_server().name == "testserver2"

    # activating a non-existant server name should just give a nice message, no crashes
    result = runner.invoke(entrypoint.cli, "server activate yomomma")
    assert "Invalid value" in result.output


def test_command_line_tool_job_functions(mock_main_runner, mock_requests):
    """Check a whole lot of commands without doing actual queries

    Kind of a mop up test trying to get coverage up
    """
    runner = mock_main_runner

    mock_requests.set_response_text(text=RequestsMockResponseExamples.JOB_INFO)
    runner.invoke(entrypoint.cli, "job info 1234")
    assert mock_requests.requests.get.called is True
    assert "1234" in str(mock_requests.requests.get.call_args)

    mock_requests.reset()
    runner.invoke(entrypoint.cli, "job reset 1234")
    assert mock_requests.requests.post.called is True
    assert "'files_downloaded': 0" in str(mock_requests.requests.post.call_args)

    mock_requests.reset()
    runner.invoke(entrypoint.cli, "job cancel 1234")
    assert mock_requests.requests.post.called is True
    assert "cancel" in str(mock_requests.requests.post.call_args)

    # can't reset a job when there is no server

    mock_main_runner.get_context().settings.active_server = None
    mock_requests.reset()
    result = runner.invoke(entrypoint.cli, "job reset 1234")
    assert mock_requests.requests.post.called is False
    assert "No active server. Which one do you want to use?" in str(result.exception)


def test_command_line_tool_job_list(mock_main_runner, mock_requests):
    runner = mock_main_runner
    mock_requests.set_response_text(
        RequestsMockResponseExamples.JOBS_LIST_GET_JOBS_LIST
    )
    result = runner.invoke(entrypoint.cli, "job list 1 2 3 445")
    assert "Z495159" in result.output
    assert "1000" in result.output
    assert "1002" in result.output
    assert "5000" in result.output


def test_job_id_parameter_type(mock_main_runner, mock_requests):
    """Test passing ID ranges such as 1000-1200 as job ids"""

    runner = mock_main_runner
    get_job_info_mock = Mock()
    mock_main_runner.get_context().client_tool.get_job_info_list = get_job_info_mock

    # test regular expansion
    result = runner.invoke(entrypoint.cli, "job list 1 2 5-10")
    assert result.exit_code == 0
    assert get_job_info_mock.call_args[1]["job_ids"] == [
        "1",
        "2",
        "5",
        "6",
        "7",
        "8",
        "9",
        "10",
    ]

    # test nothing to expand
    result = runner.invoke(entrypoint.cli, "job list 1")
    assert result.exit_code == 0
    assert get_job_info_mock.call_args[1]["job_ids"] == ["1"]

    # test overlapping ranges
    get_job_info_mock.reset()
    runner.invoke(entrypoint.cli, "job list 1-4 2-5")
    assert get_job_info_mock.call_args[1]["job_ids"] == [
        "1",
        "2",
        "3",
        "4",
        "2",
        "3",
        "4",
        "5",
    ]

    # test range and weird input argument (not sure whether this is a good idea to allow)
    get_job_info_mock.reset()
    runner.invoke(entrypoint.cli, "job list 1-4 hallo")
    assert get_job_info_mock.call_args[1]["job_ids"] == ["1", "2", "3", "4", "hallo"]


@pytest.mark.parametrize(
    "command, server_response, expected_print",
    [
        (
            "server jobs",
            RequestsMockResponseExamples.JOBS_LIST_GET_JOBS,
            "most recent 50 jobs on testserver:",
        ),
        ("status", "", "Available servers"),  # general status should not hit server
    ],
)
def test_command_line_tool_server_functions(
    mock_main_runner, mock_requests, command, server_response, expected_print
):
    """Check a whole lot of commands without doing actual queries

    Kind of a mop up test trying to get coverage up
    """
    runner = mock_main_runner
    mock_requests.set_response_text(text=server_response)
    result = runner.invoke(entrypoint.cli, command, catch_exceptions=False)
    assert expected_print in result.output


def test_get_server_when_none_is_active(mock_main_runner):
    """In certain cases active server can be None. handle this gracefully"""
    context = mock_main_runner.get_context()
    context.settings.active_server = None
    # Calling for server here should fail because there is no active server
    with pytest.raises(AnonAPIContextException):
        context.get_active_server()


def test_command_line_tool_user_commands(mock_main_runner):

    runner = mock_main_runner
    context = mock_main_runner.get_context()

    assert context.settings.user_name != "test_changed"
    runner.invoke(entrypoint.cli, "settings user set-username test_changed")
    assert context.settings.user_name == "test_changed"

    result = runner.invoke(entrypoint.cli, "settings user info", catch_exceptions=False)
    assert "user" in result.output

    token_before = context.settings.user_token
    result = runner.invoke(entrypoint.cli, "settings user get-token")
    assert "Got and saved api token" in result.output
    token_after = context.settings.user_token
    assert token_before != token_after  # token should have changed


@pytest.mark.parametrize(
    "command, mock_requests_response, expected_output",
    [
        ("server jobs", requests.exceptions.ConnectionError, "Error getting jobs"),
        ("job info 123", requests.exceptions.ConnectionError, "Error"),
        ("server status", requests.exceptions.ConnectionError, "cannot be reached",),
        (
            "job cancel 123",
            requests.exceptions.RequestException,
            "Error cancelling job",
        ),
        ("job reset 123", requests.exceptions.ConnectionError, "Error resetting job"),
        ("batch status", APIClientException, "Error getting jobs"),
        ("batch status", APIParseResponseException, "Error parsing server response"),
        ("server jobs", APIParseResponseException, "Error parsing server response"),
    ],
)
def test_client_tool_exception_response(
    mock_main_runner_with_batch,
    mock_requests,
    command,
    mock_requests_response,
    expected_output,
):
    """The client that the command line tool is using might yield exceptions.
    Handle gracefully
    """
    runner = mock_main_runner_with_batch

    # any call to server will yield error
    mock_requests.set_response_exception(
        mock_requests_response("Terrible error with " + command)
    )

    result = runner.invoke(entrypoint.cli, command.split(" "))
    assert expected_output in result.output


def test_cli_entrypoint(monkeypatch, tmpdir):
    """Call main entrypoint with empty homedir. This should create a default
    settings file
    """
    monkeypatch.setattr(
        "anonapi.cli.entrypoint.get_settings_path",
        lambda: Path(tmpdir) / "testsettings.yaml",
    )
    context = get_context()
    assert context.settings.user_name == "username"
