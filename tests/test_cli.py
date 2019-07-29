#!/usr/bin/env python
# -*- coding: utf-8 -*-
from unittest.mock import Mock

import pytest

from click.testing import CliRunner

from anonapi.batch import BatchFolder, JobBatch
from anonapi.cli import AnonClientTool, AnonCommandLineParser, AnonCommandLineParserException, ClientToolException
from anonapi.client import APIClientException
from anonapi.objects import RemoteAnonServer
from anonapi.responses import APIParseResponseException
from anonapi.settings import AnonClientSettings
from tests.factories import RequestsMock, RequestsMockResponseExamples


@pytest.fixture
def anonapi_mock_cli():
    """Returns AnonCommandLineParser object

    """
    settings = AnonClientSettings(
        servers=[RemoteAnonServer(name="testserver", url="https://testurl"),
                 RemoteAnonServer(name="testserver2", url="https://testurl2")],
        user_name="testuser",
        user_token="testtoken",
    )
    tool = AnonClientTool(username=settings.user_name, token=settings.user_token)
    return AnonCommandLineParser(client_tool=tool, settings=settings)


@pytest.fixture
def anonapi_mock_cli_with_batch(anonapi_mock_cli):
    """Returns AnonCommandLineParser object that has a batch defined

    """

    batch = JobBatch(
        job_ids=["1000", "1002", "5000", "100000"],
        server=anonapi_mock_cli.get_active_server(),
    )
    anonapi_mock_cli.get_batch = lambda: batch  # set current batch to mock batch
    return anonapi_mock_cli


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
    assert len(anonapi_mock_cli.settings.servers) == 2
    runner.invoke(
        anonapi_mock_cli.main, ["server", "add", "a_server", "https://test.com"]
    )

    assert len(anonapi_mock_cli.settings.servers) == 3
    runner.invoke(anonapi_mock_cli.main, "server remove testserver".split(" "))

    assert len(anonapi_mock_cli.settings.servers) == 2

    # removing a non-existent server should not crash but yield nice message
    result = runner.invoke(
        anonapi_mock_cli.main, "server remove non_existant_server".split(" ")
    )
    assert result.exit_code == 2
    assert "invalid choice" in str(result.output)

    with pytest.raises(AnonCommandLineParserException):
        anonapi_mock_cli.get_server_by_name("unknown_server")


def test_command_line_tool_list_servers(anonapi_mock_cli):

    runner = CliRunner()
    result = runner.invoke(
        anonapi_mock_cli.main, "server list".split(" ")
    )
    assert result.exit_code == 0
    assert all([x in result.output for x in ['Available servers', 'testserver ', 'testserver2 ']])


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


def test_cli_job_list(anonapi_mock_cli, mock_requests):
    """Try operations actually calling server"""
    runner = CliRunner()

    mock_requests.set_response(
        text=RequestsMockResponseExamples.JOBS_LIST_GET_JOBS_LIST
    )
    result = runner.invoke(anonapi_mock_cli.main, "job list 1000 1002 50000")
    assert all(
        text in result.output
        for text in ["DONE", "UPLOAD", "1000", "1002", "5000"]
    )


def test_command_line_tool_activate_server(anonapi_mock_cli, mock_requests):
    """Test activating a server"""

    runner = CliRunner()

    assert anonapi_mock_cli.get_active_server().name == "testserver"
    result = runner.invoke(anonapi_mock_cli.main, "server activate testserver2".split(" "))
    assert "Set active server to" in result.output
    assert anonapi_mock_cli.get_active_server().name == "testserver2"

    # activating a non-existant server name should just give a nice message, no crashes
    result = runner.invoke(anonapi_mock_cli.main, "server activate yomomma".split(" "))
    assert "invalid choice" in result.output


def test_command_line_tool_job_functions(anonapi_mock_cli, mock_requests):
    """Check a whole lot of commands without doing actual queries

    Kind of a mop up test trying to get coverage up"""
    runner = CliRunner()

    mock_requests.set_response(text=RequestsMockResponseExamples.JOB_INFO)
    runner.invoke(anonapi_mock_cli.main, "job info 1234".split(" "))
    assert mock_requests.requests.get.called is True
    assert "1234" in str(mock_requests.requests.get.call_args)

    mock_requests.reset()
    runner.invoke(anonapi_mock_cli.main, "job reset 1234".split(" "))
    assert mock_requests.requests.post.called is True
    assert "'files_downloaded': 0" in str(mock_requests.requests.post.call_args)

    mock_requests.reset()
    runner.invoke(anonapi_mock_cli.main, "job cancel 1234".split(" "))
    assert mock_requests.requests.post.called is True
    assert "cancel" in str(mock_requests.requests.post.call_args)

    # can't reset a job when there is no server

    anonapi_mock_cli.settings.active_server = None
    mock_requests.reset()
    result = runner.invoke(anonapi_mock_cli.main, "job reset 1234".split(" "))
    assert mock_requests.requests.post.called is False
    assert "No active server. Which one do you want to use?" in str(result.exception)


def test_command_line_tool_job_list(anonapi_mock_cli, mock_requests):
    runner = CliRunner()
    mock_requests.set_response(RequestsMockResponseExamples.JOBS_LIST_GET_JOBS_LIST)
    result = runner.invoke(anonapi_mock_cli.main, "job list 1 2 3 445".split(" "))
    assert "Z495159" in result.output
    assert "1000" in result.output
    assert "1002" in result.output
    assert "5000" in result.output


def test_job_id_parameter_type(anonapi_mock_cli, mock_requests):
    """Test passing ID ranges such as 1000-1200 as job ids"""

    runner = CliRunner()
    get_job_info_mock = Mock()
    anonapi_mock_cli.client_tool.get_job_info_list = get_job_info_mock

    # test regular expansion
    result = runner.invoke(anonapi_mock_cli.main, "job list 1 2 5-10".split(" "))
    assert result.exit_code == 0
    assert get_job_info_mock.call_args[1]['job_ids'] == ["1", "2", "5", "6", "7", "8", "9", "10", ]

    # test nothing to expand
    result = runner.invoke(anonapi_mock_cli.main, "job list 1".split(" "))
    assert result.exit_code == 0
    assert get_job_info_mock.call_args[1]['job_ids'] == ["1"]

    # test overlapping ranges
    get_job_info_mock.reset()
    runner.invoke(anonapi_mock_cli.main, "job list 1-4 2-5".split(" "))
    assert get_job_info_mock.call_args[1]['job_ids'] == ["1", "2", "3", "4", "2", "3", "4", "5", ]

    # test range and weird string argument (not sure whether this is a good idea to allow)
    get_job_info_mock.reset()
    runner.invoke(anonapi_mock_cli.main, "job list 1-4 hallo".split(" "))
    assert get_job_info_mock.call_args[1]['job_ids'] == ["1", "2", "3", "4", "hallo"]


@pytest.mark.parametrize(
    "command, server_response, expected_print",
    [
        (
            "server jobs".split(" "),
            RequestsMockResponseExamples.JOBS_LIST_GET_JOBS,
            "most recent 50 jobs on testserver:",
        ),
        (
            "status".split(" "),
            "",
            "Available servers",
        ),  # general status should not hit server
    ],
)
def test_command_line_tool_server_functions(
    anonapi_mock_cli,
    mock_requests,
    command,
    server_response,
    expected_print,
):
    """Check a whole lot of commands without doing actual queries

    Kind of a mop up test trying to get coverage up"""
    runner = CliRunner()
    mock_requests.set_response(text=server_response)
    result = runner.invoke(anonapi_mock_cli.main, command)
    assert expected_print in result.output


def test_get_server_when_none_is_active(anonapi_mock_cli):
    """In certain cases active server can be None. handle this gracefully

    """
    anonapi_mock_cli.settings.active_server = None
    # Calling for server here should fail because there is no active server
    with pytest.raises(AnonCommandLineParserException):
        anonapi_mock_cli.get_active_server()


def test_command_line_tool_user_functions(
    anonapi_mock_cli
):
    runner = CliRunner()
    assert anonapi_mock_cli.settings.user_name != "test_changed"

    runner.invoke(anonapi_mock_cli.main, "user set-username test_changed".split(" "))
    assert anonapi_mock_cli.settings.user_name == "test_changed"

    result = runner.invoke(anonapi_mock_cli.main, "user info".split(" "))
    assert "user" in result.output

    token_before = anonapi_mock_cli.settings.user_token
    result = runner.invoke(anonapi_mock_cli.main, "user get-token".split(" "))
    assert "Got and saved api token" in result.output
    token_after = anonapi_mock_cli.settings.user_token
    assert token_before != token_after  # token should have changed


@pytest.mark.parametrize(
    "command, mock_requests_response, expected_output",
    [
        ("server jobs", ConnectionError, "Error getting jobs"),
        ("job info 123", ConnectionError, "Error getting job info"),
        ("server status", ConnectionError, "is not responding properly"),
        ("job cancel 123", ConnectionError, "Error cancelling job"),
        ("job reset 123", ConnectionError, "Error resetting job"),
        ("server status", ConnectionError, "is not responding properly"),
        ("batch status", APIClientException, "Error getting jobs"),
        ("batch status", APIParseResponseException, "Error parsing server response"),
        ("server jobs", APIParseResponseException, "Error parsing server response")
    ],
)
def test_client_tool_exception_response(
    anonapi_mock_cli_with_batch, mock_requests, command, mock_requests_response, expected_output
):
    """The client that the command line tool is using might yield exceptions. Handle gracefully

    """
    runner = CliRunner()

    # any call to server will yield error
    mock_requests.set_response_exception(mock_requests_response("Terrible error with " + command))

    result = runner.invoke(anonapi_mock_cli_with_batch.main, command.split(" "))
    assert expected_output in result.output


def test_cli_batch(anonapi_mock_cli, tmpdir):
    """Try working with a batch of job ids from console"""
    anonapi_mock_cli.current_dir = lambda: str(
        tmpdir
    )  # make parser thinks tmpdir is its working dir

    runner = CliRunner()

    result = runner.invoke(anonapi_mock_cli.main, "batch info".split(" "))
    assert "No batch defined" in str(result.exception)

    assert not BatchFolder(tmpdir).has_batch()
    runner.invoke(anonapi_mock_cli.main, "batch init".split(" "))
    assert BatchFolder(tmpdir).has_batch()

    # init again should fail as there is already a batch defined
    result = runner.invoke(anonapi_mock_cli.main, "batch init".split(" "))
    assert "Cannot init" in str(result.exception)

    runner.invoke(anonapi_mock_cli.main, "batch add 1 2 3 345".split(" "))
    assert BatchFolder(tmpdir).load().job_ids == ["1", "2", "3", "345"]

    runner.invoke(anonapi_mock_cli.main,
                  "batch add 1 2 50".split(" ")
                  )  # duplicates should be silently ignored
    assert BatchFolder(tmpdir).load().job_ids == ["1", "2", "3", "345", "50"]

    runner.invoke(anonapi_mock_cli.main,
                  "batch remove 50 345 1000".split(" ")
                  )  # non-existing keys should be ignored
    assert BatchFolder(tmpdir).load().job_ids == ["1", "2", "3"]

    runner.invoke(anonapi_mock_cli.main, "batch remove 1 2 3".split(" "))
    assert BatchFolder(tmpdir).load().job_ids == []

    runner.invoke(anonapi_mock_cli.main, "batch delete".split(" "))
    assert not BatchFolder(tmpdir).has_batch()


def test_cli_batch_status(anonapi_mock_cli, mock_requests):
    """Try operations actually calling server"""
    runner = CliRunner()

    batch = JobBatch(
        job_ids=["1000", "1002", "5000"], server=anonapi_mock_cli.get_active_server()
    )
    anonapi_mock_cli.get_batch = lambda: batch  # set current batch to mock batch

    mock_requests.set_response(
        text=RequestsMockResponseExamples.JOBS_LIST_GET_JOBS_LIST
    )
    result = runner.invoke(anonapi_mock_cli.main, "batch status")
    assert all(
        text in result.output
        for text in ["DONE", "UPLOAD", "1000", "1002", "5000"]
    )


def test_cli_batch_cancel(anonapi_mock_cli_with_batch, mock_requests):
    """Try operations actually calling server"""
    runner = CliRunner()

    mock_requests.set_response(
        text=RequestsMockResponseExamples.JOBS_LIST_GET_JOBS_LIST
    )
    result = runner.invoke(anonapi_mock_cli_with_batch.main, "batch cancel", input="No")
    assert 'User cancelled' in result.output
    assert not mock_requests.requests.called

    mock_requests.reset()
    result = runner.invoke(anonapi_mock_cli_with_batch.main, "batch cancel", input="Yes")
    assert 'Cancelled job 1000' in result.output
    assert mock_requests.requests.post.call_count == 4


def test_cli_batch_status_errors(anonapi_mock_cli_with_batch, mock_requests):
    """Call server, but not all jobs exist. This should appear in the status message to the user"""
    runner = CliRunner()

    mock_requests.set_response(
        text=RequestsMockResponseExamples.JOBS_LIST_GET_JOBS_LIST
    )

    result = runner.invoke(anonapi_mock_cli_with_batch.main, "batch status")
    assert "NOT_FOUND    1" in result.output


def test_cli_batch_reset(anonapi_mock_cli_with_batch, mock_requests):

    runner = CliRunner()

    runner.invoke(anonapi_mock_cli_with_batch.main, "batch reset", input="Yes")
    assert mock_requests.requests.post.call_count == 4  # Reset request should have been sent for each job id

    mock_requests.requests.reset_mock()
    runner.invoke(anonapi_mock_cli_with_batch.main, "batch reset", input="No")  # now answer no when asked are you sure
    assert mock_requests.requests.post.call_count == 0  # No requests should have been sent


def test_cli_batch_reset_error(anonapi_mock_cli_with_batch, mock_requests):
    """Try operations actually calling server"""
    runner = CliRunner()

    mock_requests.set_response(
        text=RequestsMockResponseExamples.JOBS_LIST_GET_JOBS_LIST_WITH_ERROR
    )

    # try a reset, answer 'Yes' to question
    result = runner.invoke(anonapi_mock_cli_with_batch.main, "batch reset-error".split(" "), input='Yes')
    assert result.exit_code == 0
    assert 'This will reset 2 jobs on testserver' in result.output
    assert 'Done' in result.output
    assert mock_requests.requests.post.called

    # now try the same but answer 'No'
    mock_requests.reset()
    result = runner.invoke(anonapi_mock_cli_with_batch.main, "batch reset-error".split(" "), input='No')
    assert result.exit_code == 0
    assert not mock_requests.requests.post.called   # cancelling should not have sent any requests

    # A reset where the server returns error
    mock_requests.reset()
    mock_requests.set_response_exception(ClientToolException("Terrible exception"))
    result = runner.invoke(anonapi_mock_cli_with_batch.main, "batch reset-error".split(" "))
    assert 'Error resetting:' in result.output


def test_cli_batch_id_range(anonapi_mock_cli, tmpdir):
    """check working with id ranges"""
    anonapi_mock_cli.current_dir = lambda: str(
        tmpdir
    )  # make parser thinks tmpdir is its working dir

    runner = CliRunner()

    assert not BatchFolder(tmpdir).has_batch()
    runner.invoke(anonapi_mock_cli.main, "batch init".split(" "))
    assert BatchFolder(tmpdir).has_batch()

    runner.invoke(anonapi_mock_cli.main, "batch add 1 2 5-8".split(" "))
    assert BatchFolder(tmpdir).load().job_ids == ["1", "2", "5", "6", "7", "8"]

    runner.invoke(anonapi_mock_cli.main, "batch remove 1-4".split(" "))
    assert BatchFolder(tmpdir).load().job_ids == ["5", "6", "7", "8"]

    runner.invoke(anonapi_mock_cli.main, "batch add 1-4 4".split(" "))  # check that duplicate values do not cause trouble
    assert BatchFolder(tmpdir).load().job_ids == ["1", "2", "3", "4", "5", "6", "7", "8"]

