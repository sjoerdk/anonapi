#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for the `anonapi.anon` module."""
from unittest.mock import patch, Mock

import pytest
from pytest import fixture

from anonapi.anon import AnonCommandLineParser, AnonClientTool, AnonCommandLineParserException
from anonapi.objects import RemoteAnonServer
from anonapi.settings import DefaultAnonClientSettings


class NonPrintingAnonCommandLineParser(AnonCommandLineParser):
    """For test purposes. Just to indicate that this class has a mock_console attribute"""
    mock_console = None


class MockConsole:
    """A console with a print function that just records

    """
    def __init__(self):
        self.content = []

    def print(self, msg):
        self.content.append(msg)

    def all_content(self):
        return "\n".join(self.content)

    def last_print(self):
        return self.content[-1]

    def assert_called(self):
        assert self.content


@fixture
def non_printing_test_parser():
    """A command line tool instance with a Mock() client tool, so no actual calls are made.
    Also, printing to console instead logged to mock_console

    Returns
    -------
    AnonCommandLineParser with additional field 'mock_console' that records output

    """
    settings = DefaultAnonClientSettings()
    parser = NonPrintingAnonCommandLineParser(client_tool=Mock(), settings=settings)

    parser.mock_console = MockConsole()
    parser.print_to_console = parser.mock_console.print
    return parser


@fixture
def extended_non_printing_test_parser(non_printing_test_parser: NonPrintingAnonCommandLineParser):
    """A parser that does not actually print to console, seeded with different servers"""

    settings = non_printing_test_parser.settings
    settings.servers.append(RemoteAnonServer(name='sandbox', url='https://umcradanonp11.umcn.nl/sandbox'))
    settings.servers.append(RemoteAnonServer(name='wrong', url='https://umcradanonp11.umcn.nl/non_existant'))
    settings.servers.append(RemoteAnonServer(name='p01', url='https://umcradanonp11.umcn.nl/p01'))

    return non_printing_test_parser


def test_command_line_tool_basic(non_printing_test_parser: NonPrintingAnonCommandLineParser):
    """Test some commands"""
    non_printing_test_parser.execute_command("status".split(" "))

    assert 'Available servers' in non_printing_test_parser.mock_console.all_content()


def test_command_line_tool_status_without_active_server(non_printing_test_parser: NonPrintingAnonCommandLineParser):
    """Error found live, making sure its fixed """
    non_printing_test_parser.settings.active_server = None

    # this should not crash
    non_printing_test_parser.get_status()


@pytest.mark.parametrize('command, expected_server_list_length', [
    ("server list".split(" "), 1),  # you start with one server
    ("server add server2 https://something.com".split(" "), 2),  # after adding a server you should have two
    ("server remove test".split(" "), 0)  # if you remove it there should be none
])
def test_command_line_tool_add_remove_server(non_printing_test_parser: NonPrintingAnonCommandLineParser, command,
                                             expected_server_list_length):
    """Test commands to add, remove servers and see whether the number servers that are known is correct"""
    non_printing_test_parser.execute_command(command)
    assert len(non_printing_test_parser.settings.servers) == expected_server_list_length


def test_command_line_tool_server_status(extended_non_printing_test_parser: NonPrintingAnonCommandLineParser):
    """Test checking status"""

    # this should not crash
    extended_non_printing_test_parser.execute_command("server status p01".split(" "))
    assert extended_non_printing_test_parser.mock_console.all_content()


def test_command_line_tool_job_info(extended_non_printing_test_parser: NonPrintingAnonCommandLineParser):
    """Test checking status"""

    extended_non_printing_test_parser.execute_command("server activate sandbox".split(" "))
    assert "Set active server to" in extended_non_printing_test_parser.mock_console.last_print()

    extended_non_printing_test_parser.execute_command("job info 10".split(" "))
    extended_non_printing_test_parser.mock_console.assert_called()

    # nothing should have crashed, and something should have been written. Better then nothing.
    assert extended_non_printing_test_parser.mock_console


def test_command_line_tool_activate_server(extended_non_printing_test_parser: NonPrintingAnonCommandLineParser):
    """Test activating a server"""
    extended_non_printing_test_parser.execute_command("server activate sandbox".split(" "))
    assert extended_non_printing_test_parser.get_active_server().name == 'sandbox'

    # activate a non-existant server name should just give a nice message, no crashes
    extended_non_printing_test_parser.execute_command("server activate yomomma".split(" "))
    assert 'Unknown server' in extended_non_printing_test_parser.mock_console.last_print()
    assert extended_non_printing_test_parser.get_active_server().name == 'sandbox'


def test_command_line_tool_job_functions(extended_non_printing_test_parser: NonPrintingAnonCommandLineParser):
    """Check a whole lot of commands without doing actual queries

    Kind of a mop up test trying to get coverage up"""

    extended_non_printing_test_parser.execute_command("job info 1234".split(" "))
    assert extended_non_printing_test_parser.client_tool.method_calls

    extended_non_printing_test_parser.execute_command("job reset 1234".split(" "))
    assert extended_non_printing_test_parser.client_tool.method_calls

    extended_non_printing_test_parser.execute_command("job cancel 1234".split(" "))
    assert extended_non_printing_test_parser.client_tool.method_calls

    # can't reset a job when there is no server
    extended_non_printing_test_parser.settings.active_server = None
    extended_non_printing_test_parser.client_tool.reset_mock()
    extended_non_printing_test_parser.execute_command("job reset 1234".split(" "))
    assert not extended_non_printing_test_parser.client_tool.method_calls


@pytest.mark.parametrize('command, expected_client_to_be_called', [
    ("server jobs".split(" "), True),
    ("server jobs no-server".split(" "), False),  # server no-server does not exist. No calls to client expected
    ("server status test".split(" "), True),  # server test exists, should work
    ("status".split(" "), False),  # general status should not hit server
])
def test_command_line_tool_server_functions(extended_non_printing_test_parser: NonPrintingAnonCommandLineParser,
                                            command, expected_client_to_be_called):
    """Check a whole lot of commands without doing actual queries

    Kind of a mop up test trying to get coverage up"""
    extended_non_printing_test_parser.execute_command(command)
    assert expected_client_to_be_called == bool(extended_non_printing_test_parser.client_tool.method_calls)


def test_get_server_when_none_is_active(extended_non_printing_test_parser: NonPrintingAnonCommandLineParser):
    """In certain cases active server can be None. handle this gracefully

    """
    extended_non_printing_test_parser.settings.active_server = None
    #Calling for server here should fail because there is no active server
    with pytest.raises(AnonCommandLineParserException):
        extended_non_printing_test_parser.get_active_server()


def test_command_line_tool_user_functions(extended_non_printing_test_parser: NonPrintingAnonCommandLineParser):

    assert extended_non_printing_test_parser.settings.user_name != "test_changed"

    extended_non_printing_test_parser.execute_command("user set_username test_changed".split(" "))
    assert extended_non_printing_test_parser.settings.user_name == "test_changed"




