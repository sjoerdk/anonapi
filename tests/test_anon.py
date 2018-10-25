#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `anonapi` package."""
from unittest.mock import patch, Mock

import pytest
from pytest import fixture

from anonapi.anon import DefaultAnonClientSettings, AnonCommandLineParser, AnonClientTool, RemoteAnonServer


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
    client_tool = Mock()
    settings = DefaultAnonClientSettings()
    parser = NonPrintingAnonCommandLineParser(client_tool=client_tool, settings=settings)

    parser.mock_console = MockConsole()
    parser.print_to_console = parser.mock_console.print
    return parser


@fixture
def extended_non_printing_test_parser(non_printing_test_parser: NonPrintingAnonCommandLineParser):
    """A parser that does not actually print to console, seeded with different servers and can return some fake
    job info """

    non_printing_test_parser.client_tool.get_job_info.return_value = "{'job_id': 1}"  # return some fake job info

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
    assert "job_id" in extended_non_printing_test_parser.mock_console.last_print()

    # nothing should have crashed, and something should have been written. Better then nothing.
    assert extended_non_printing_test_parser.mock_console
