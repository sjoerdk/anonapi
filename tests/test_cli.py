#!/usr/bin/env python
# -*- coding: utf-8 -*-
import shutil
from unittest.mock import Mock

import pytest
from click.testing import CliRunner

from anonapi.batch import BatchFolder, JobBatch
from anonapi.cli import entrypoint, user_commands
from anonapi.cli.entrypoint import get_parser
from anonapi.cli.parser import (
    AnonCommandLineParserException,
)
from anonapi.client import APIClientException, ClientToolException
from anonapi.mapper import MappingListFolder, MappingLoadError
from anonapi.responses import APIParseResponseException
from tests import RESOURCE_PATH
from tests.factories import RequestsMock, RequestsMockResponseExamples


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


@pytest.fixture
def mock_anonapi_current_dir(anonapi_mock_cli, tmpdir):
    """Anonapi instance with a tempdir current dir. So you can create, read files in 'current dir'"""
    anonapi_mock_cli.current_dir = lambda: str(
        tmpdir
    )  # make mock_context thinks tmpdir is its working dir
    return anonapi_mock_cli


def test_command_line_tool_basic(anonapi_mock_cli):
    """Test most basic invocation"""

    runner = CliRunner()
    result = runner.invoke(entrypoint.cli)
    assert result.exit_code == 0
    assert "anonymization web API tool" in result.stdout


def test_command_line_tool_status_without_active_server(anonapi_mock_cli):
    """Error found live, making sure its fixed """
    anonapi_mock_cli.settings.active_server = None
    runner = CliRunner()

    # this should not crash
    result = runner.invoke(entrypoint.cli, "status")

    assert result.exit_code == 0
    assert "Available servers" in result.stdout


def test_command_line_tool_add_remove_server(anonapi_mock_cli):
    """Test commands to add, remove servers and see whether the number servers that are known is correct"""

    runner = CliRunner()
    assert len(anonapi_mock_cli.settings.servers) == 2
    runner.invoke(entrypoint.cli, "server add a_server https://test.com")

    assert len(anonapi_mock_cli.settings.servers) == 3
    runner.invoke(entrypoint.cli, "server remove testserver")

    assert len(anonapi_mock_cli.settings.servers) == 2

    # removing a non-existent server should not crash but yield nice message
    result = runner.invoke(entrypoint.cli, "server remove non_existant_server")
    assert result.exit_code == 2
    assert "Invalid value" in str(result.output)

    with pytest.raises(AnonCommandLineParserException):
        anonapi_mock_cli.get_server_by_name("unknown_server")


def test_command_line_tool_list_servers(anonapi_mock_cli):

    runner = CliRunner()
    result = runner.invoke(entrypoint.cli, "server list")
    assert result.exit_code == 0
    assert all(
        [
            x in result.output
            for x in ["Available servers", "testserver ", "testserver2 "]
        ]
    )


def test_command_line_tool_server_status(anonapi_mock_cli, mock_requests):
    """Test checking status"""

    runner = CliRunner()

    # basic check. Call a server that responds with an expected anonapi json response
    # API_CALL_NOT_DEFINED is a response that is used to check the liveness of a server currently.
    mock_requests.set_response_text(RequestsMockResponseExamples.API_CALL_NOT_DEFINED)
    result = runner.invoke(entrypoint.cli, ["server", "status"])

    assert "OK" in result.output
    assert mock_requests.requests.get.call_count == 1

    # now test a non-responsive server:
    mock_requests.reset()
    mock_requests.set_response_exception(ConnectionError)
    result = runner.invoke(entrypoint.cli, ["server", "status"])

    assert "ERROR" in result.output
    assert mock_requests.requests.get.call_count == 1

    # now test a server that exists but responds weirdly:
    mock_requests.reset()
    mock_requests.set_response_text("Hello, welcome to an unrelated server")
    result = runner.invoke(entrypoint.cli, ["server", "status"])

    assert "is not responding properly" in result.output
    assert mock_requests.requests.get.call_count == 1


def test_command_line_tool_job_info(anonapi_mock_cli, mock_requests):
    """Test checking status"""
    runner = CliRunner()

    result = runner.invoke(entrypoint.cli, "server activate testserver")
    assert "Set active server to" in result.output

    mock_requests.set_response_text(RequestsMockResponseExamples.JOB_INFO)
    result = runner.invoke(entrypoint.cli, "job info 3")
    assert "job 3 on testserver" in result.output
    assert "'user_name', 'z123sandbox'" in result.output


def test_cli_job_list(anonapi_mock_cli, mock_requests):
    """Try operations actually calling server"""
    runner = CliRunner()

    mock_requests.set_response_text(
        text=RequestsMockResponseExamples.JOBS_LIST_GET_JOBS_LIST
    )
    result = runner.invoke(entrypoint.cli, "job list 1000 1002 50000")
    assert all(
        text in result.output for text in ["DONE", "UPLOAD", "1000", "1002", "5000"]
    )


def test_cli_job_list_errors(anonapi_mock_cli, mock_requests):
    """Giving no parameters should yield helpful error string. Not python stacktrace"""
    runner = CliRunner()
    mock_requests.set_response_text(
        text=RequestsMockResponseExamples.REQUIRED_PARAMETER_NOT_SUPPLIED,
        status_code=400
    )
    result = runner.invoke(entrypoint.cli, "job list")
    result.exit_code == 0


def test_command_line_tool_activate_server(anonapi_mock_cli, mock_requests):
    """Test activating a server"""

    runner = CliRunner()

    assert anonapi_mock_cli.get_active_server().name == "testserver"
    result = runner.invoke(entrypoint.cli, "server activate testserver2")
    assert "Set active server to" in result.output
    assert anonapi_mock_cli.get_active_server().name == "testserver2"

    # activating a non-existant server name should just give a nice message, no crashes
    result = runner.invoke(entrypoint.cli, "server activate yomomma")
    assert "Invalid value" in result.output


def test_command_line_tool_job_functions(anonapi_mock_cli, mock_requests):
    """Check a whole lot of commands without doing actual queries

    Kind of a mop up test trying to get coverage up"""
    runner = CliRunner()

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

    anonapi_mock_cli.settings.active_server = None
    mock_requests.reset()
    result = runner.invoke(entrypoint.cli, "job reset 1234")
    assert mock_requests.requests.post.called is False
    assert "No active server. Which one do you want to use?" in str(result.exception)


def test_command_line_tool_job_list(anonapi_mock_cli, mock_requests):
    runner = CliRunner()
    mock_requests.set_response_text(RequestsMockResponseExamples.JOBS_LIST_GET_JOBS_LIST)
    result = runner.invoke(entrypoint.cli, "job list 1 2 3 445")
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

    # test range and weird string argument (not sure whether this is a good idea to allow)
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
    anonapi_mock_cli, mock_requests, command, server_response, expected_print
):
    """Check a whole lot of commands without doing actual queries

    Kind of a mop up test trying to get coverage up"""
    runner = CliRunner()
    mock_requests.set_response_text(text=server_response)
    result = runner.invoke(entrypoint.cli, command)
    assert expected_print in result.output


def test_get_server_when_none_is_active(anonapi_mock_cli):
    """In certain cases active server can be None. handle this gracefully

    """
    anonapi_mock_cli.settings.active_server = None
    # Calling for server here should fail because there is no active server
    with pytest.raises(AnonCommandLineParserException):
        anonapi_mock_cli.get_active_server()


def test_command_line_tool_user_commands(anonapi_mock_cli):

    runner = CliRunner()

    assert anonapi_mock_cli.settings.user_name != "test_changed"
    runner.invoke(entrypoint.cli, "user set-username test_changed")
    assert anonapi_mock_cli.settings.user_name == "test_changed"

    result = runner.invoke(entrypoint.cli, "user info")
    assert "user" in result.output

    token_before = anonapi_mock_cli.settings.user_token
    result = runner.invoke(entrypoint.cli, "user get-token")
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
        ("server jobs", APIParseResponseException, "Error parsing server response"),
    ],
)
def test_client_tool_exception_response(
    anonapi_mock_cli_with_batch,
    mock_requests,
    command,
    mock_requests_response,
    expected_output,
):
    """The client that the command line tool is using might yield exceptions. Handle gracefully

    """
    runner = CliRunner()

    # any call to server will yield error
    mock_requests.set_response_exception(
        mock_requests_response("Terrible error with " + command)
    )

    result = runner.invoke(entrypoint.cli, command.split(" "))
    assert expected_output in result.output


def test_cli_batch(anonapi_mock_cli, tmpdir):
    """Try working with a batch of job ids from console"""
    anonapi_mock_cli.current_dir = lambda: str(
        tmpdir
    )  # make mock_context thinks tmpdir is its working dir

    runner = CliRunner()

    result = runner.invoke(entrypoint.cli, "batch info")
    assert "No batch defined" in str(result.output)

    assert not BatchFolder(tmpdir).has_batch()
    runner.invoke(entrypoint.cli, "batch init")
    assert BatchFolder(tmpdir).has_batch()

    # init again should fail as there is already a batch defined
    result = runner.invoke(entrypoint.cli, "batch init")
    assert "Cannot init" in str(result.exception)

    runner.invoke(entrypoint.cli, "batch add 1 2 3 345")
    assert BatchFolder(tmpdir).load().job_ids == ["1", "2", "3", "345"]

    runner.invoke(
        entrypoint.cli, "batch add 1 2 50"
    )  # duplicates should be silently ignored
    assert BatchFolder(tmpdir).load().job_ids == ["1", "2", "3", "345", "50"]

    runner.invoke(
        entrypoint.cli, "batch remove 50 345 1000"
    )  # non-existing keys should be ignored
    assert BatchFolder(tmpdir).load().job_ids == ["1", "2", "3"]

    runner.invoke(entrypoint.cli, "batch remove 1 2 3")
    assert BatchFolder(tmpdir).load().job_ids == []

    runner.invoke(entrypoint.cli, "batch delete")
    assert not BatchFolder(tmpdir).has_batch()


def test_cli_batch_status(anonapi_mock_cli, mock_requests):
    """Try operations actually calling server"""
    runner = CliRunner()

    batch = JobBatch(
        job_ids=["1000", "1002", "5000"], server=anonapi_mock_cli.get_active_server()
    )
    anonapi_mock_cli.get_batch = lambda: batch  # set current batch to mock batch

    mock_requests.set_response_text(
        text=RequestsMockResponseExamples.JOBS_LIST_GET_JOBS_LIST
    )
    result = runner.invoke(entrypoint.cli, "batch status")
    assert all(
        text in result.output for text in ["DONE", "UPLOAD", "1000", "1002", "5000"]
    )


def test_cli_batch_cancel(anonapi_mock_cli_with_batch, mock_requests):
    """Try operations actually calling server"""
    runner = CliRunner()

    mock_requests.set_response_text(
        text=RequestsMockResponseExamples.JOBS_LIST_GET_JOBS_LIST
    )
    result = runner.invoke(entrypoint.cli, "batch cancel", input="No")
    assert "User cancelled" in result.output
    assert not mock_requests.requests.called

    mock_requests.reset()
    result = runner.invoke(entrypoint.cli, "batch cancel", input="Yes")
    assert "Cancelled job 1000" in result.output
    assert mock_requests.requests.post.call_count == 4


def test_cli_batch_status_errors(anonapi_mock_cli_with_batch, mock_requests):
    """Call server, but not all jobs exist. This should appear in the status message to the user"""
    runner = CliRunner()

    mock_requests.set_response_text(
        text=RequestsMockResponseExamples.JOBS_LIST_GET_JOBS_LIST
    )
    result = runner.invoke(entrypoint.cli, "batch status")
    assert "NOT_FOUND    1" in result.output


def test_cli_batch_reset(anonapi_mock_cli_with_batch, mock_requests):

    runner = CliRunner()

    runner.invoke(entrypoint.cli, "batch reset", input="Yes")
    assert (
        mock_requests.requests.post.call_count == 4
    )  # Reset request should have been sent for each job id

    mock_requests.requests.reset_mock()
    runner.invoke(
        entrypoint.cli, "batch reset", input="No"
    )  # now answer no when asked are you sure
    assert (
        mock_requests.requests.post.call_count == 0
    )  # No requests should have been sent


def test_cli_batch_reset_error(anonapi_mock_cli_with_batch, mock_requests):
    """Try operations actually calling server"""
    runner = CliRunner()

    mock_requests.set_response_text(
        text=RequestsMockResponseExamples.JOBS_LIST_GET_JOBS_LIST_WITH_ERROR
    )

    # try a reset, answer 'Yes' to question
    result = runner.invoke(entrypoint.cli, "batch reset-error", input="Yes")
    assert result.exit_code == 0
    assert "This will reset 2 jobs on testserver" in result.output
    assert "Done" in result.output
    assert mock_requests.requests.post.called

    # now try the same but answer 'No'
    mock_requests.reset()
    result = runner.invoke(entrypoint.cli, "batch reset-error", input="No")
    assert result.exit_code == 0
    assert (
        not mock_requests.requests.post.called
    )  # cancelling should not have sent any requests

    # A reset where the server returns error
    mock_requests.reset()
    mock_requests.set_response_exception(ClientToolException("Terrible exception"))
    result = runner.invoke(entrypoint.cli, "batch reset-error")
    assert "Error resetting:" in result.output


def test_cli_batch_id_range(anonapi_mock_cli, tmpdir):
    """check working with id ranges"""
    anonapi_mock_cli.current_dir = lambda: str(
        tmpdir
    )  # make mock_context thinks tmpdir is its working dir

    runner = CliRunner()

    assert not BatchFolder(tmpdir).has_batch()
    runner.invoke(entrypoint.cli, "batch init")
    assert BatchFolder(tmpdir).has_batch()

    runner.invoke(entrypoint.cli, "batch add 1 2 5-8")
    assert BatchFolder(tmpdir).load().job_ids == ["1", "2", "5", "6", "7", "8"]

    runner.invoke(entrypoint.cli, "batch remove 1-4")
    assert BatchFolder(tmpdir).load().job_ids == ["5", "6", "7", "8"]

    runner.invoke(
        entrypoint.cli, "batch add 1-4 4"
    )  # check that duplicate values do not cause trouble
    assert BatchFolder(tmpdir).load().job_ids == [
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
    ]


def test_cli_map(mock_anonapi_current_dir):
    runner = CliRunner()
    result = runner.invoke(entrypoint.cli, "map init")
    assert result.exit_code == 0


def test_cli_map_info(anon_mock_cli_with_mapping):
    """running map info should give you a nice print of contents"""
    anon_mock_cli_with_mapping.current_dir = lambda: RESOURCE_PATH / "test_cli"

    runner = CliRunner()
    result = runner.invoke(entrypoint.cli, "map status")

    assert result.exit_code == 0
    assert "file16/nogiets" in result.output


def test_cli_map_info_empty_dir(mock_anonapi_current_dir):
    """running info on a directory not containing a mapping file should yield a nice 'no mapping' message"""
    runner = CliRunner()
    result = runner.invoke(entrypoint.cli, "map status")

    assert result.exit_code == 0
    assert "No mapping defined" in result.output


def test_cli_map_info_load_exception(anonapi_mock_cli, monkeypatch):
    """running info with a corrupt mapping file should yield a nice message"""
    # make sure a valid mapping file is found
    anonapi_mock_cli.current_dir = lambda: str(RESOURCE_PATH / "test_cli")

    # but then raise exception when loading
    def mock_load(x):
        raise MappingLoadError("Test Exception")

    monkeypatch.setattr("anonapi.mapper.MappingList.load", mock_load)
    runner = CliRunner()

    result = runner.invoke(entrypoint.cli, "map status")

    assert result.exit_code == 0
    assert "Test Exception" in result.output


def test_cli_map_info_empty_dir(mock_anonapi_current_dir):
    """running info on a directory not containing a mapping file should yield a nice 'no mapping' message"""
    runner = CliRunner()
    result = runner.invoke(entrypoint.cli, "map status")

    assert result.exit_code == 0
    assert "No mapping defined" in result.output


def test_cli_map_add_folder(anonapi_mock_cli, folder_with_some_dicom_files):
    """Add a folder with some dicom files to a mapping."""
    # copy some content to tmp location
    selection_folder = folder_with_some_dicom_files

    # Add this folder to mapping
    runner = CliRunner()
    result = runner.invoke(
        entrypoint.cli, f"map add-study-folder {selection_folder.path}",
        catch_exceptions=False
    )

    # oh no! no mapping yet!
    assert "No mapping defined" in result.output

    # make one
    runner.invoke(entrypoint.cli, f"map init")

    # dicom files should not have been selected yet currently
    assert not selection_folder.has_file_selection()
    result = runner.invoke(
        entrypoint.cli, f"map add-study-folder {selection_folder.path}"
    )
    assert selection_folder.has_file_selection()


def test_cli_map_delete(anon_mock_cli_with_mapping):
    """running map info should give you a nice print of contents"""
    mapping_folder = MappingListFolder(anon_mock_cli_with_mapping.current_dir())
    assert mapping_folder.has_mapping_list()

    runner = CliRunner()
    result = runner.invoke(entrypoint.cli, "map delete")

    assert result.exit_code == 0
    assert not mapping_folder.has_mapping_list()

    # deleting  again will yield nice message
    result = runner.invoke(entrypoint.cli, "map delete")
    assert result.exit_code == 0
    assert "No mapping defined" in result.output


def test_cli_map_edit(anon_mock_cli_with_mapping, monkeypatch):
    mock_launch = Mock()
    monkeypatch.setattr('anonapi.cli.select_commands.click.launch', mock_launch)

    runner = CliRunner()
    result = runner.invoke(entrypoint.cli, "map edit")

    assert result.exit_code == 0
    assert mock_launch.called

    # now try edit without any mapping being present
    mock_launch.reset_mock()
    runner.invoke(entrypoint.cli, "map delete")
    result = runner.invoke(entrypoint.cli, "map edit")

    assert result.exit_code == 0
    assert "No mapping file defined" in result.output
    assert not mock_launch.called


def test_cli_entrypoint(monkeypatch, tmpdir):
    """Call main entrypoint with empty homedir. This should create a default settings file"""
    monkeypatch.setattr('anonapi.cli.entrypoint.pathlib.Path.home', lambda: tmpdir)
    parser = get_parser()
    assert parser.settings.user_name == 'username'

