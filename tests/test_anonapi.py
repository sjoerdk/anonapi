#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `anonapi` package."""
from unittest.mock import patch, Mock

from pytest import fixture

from anonapi.anon import DefaultAnonClientSettings, AnonCommandLineParser


@fixture
def default_client_tool():
    """A client tool instance with a Mock() client tool, so no actual calls are made

    """
    client_tool_mock = Mock()
    settings = DefaultAnonClientSettings()
    return AnonCommandLineParser(client_tool=client_tool_mock, settings=settings)

@fixture
def mock_console():
    """A console with a print function that just records

    """
    class MockConsole():
        def __init__(self):
            self.content = []

        def print(self, msg):
            self.content.append(msg)

        def all_content(self):
            return "\n".join(self.content)

    return MockConsole()


#  @patch('sys.stdout')  # catch print statements to keep test output clean
#  @patch('anonymization.anon.AnonCommandLineParser.get_status')  # catch print statements to keep test output clean
def test_command_line_tool_basic(default_client_tool: AnonCommandLineParser, mock_console):
    """Test some commands"""

    default_client_tool.print_to_console = mock_console.print
    default_client_tool.execute_command("status".split(" "))

    assert 'Available servers' in mock_console.all_content()
