#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest

from click.testing import CliRunner

from anonapi.cli import AnonClientTool, AnonCommandLineParser, AnonCommandLineParserException
from anonapi.objects import RemoteAnonServer
from anonapi.settings import AnonClientSettings


@pytest.fixture
def anonapi_mock_cli():
    """Returns AnonCommandLineParser object

    """
    settings = AnonClientSettings(servers=[RemoteAnonServer(name='testserver', url='https://testurl')],
                                  user_name='testuser',
                                  user_token='testtoken')
    tool = AnonClientTool(username=settings.user_name, token=settings.user_token)
    return AnonCommandLineParser(client_tool=tool, settings=settings)


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
    result = runner.invoke(anonapi_mock_cli.main, ['status'])

    assert result.exit_code == 0
    assert "Available servers" in result.stdout


def test_command_line_tool_add_remove_server(anonapi_mock_cli):
    """Test commands to add, remove servers and see whether the number servers that are known is correct"""

    runner = CliRunner()
    assert len(anonapi_mock_cli.settings.servers) == 1
    runner.invoke(anonapi_mock_cli.main, ['server', 'add', 'a_server', 'https://test.com'])

    assert len(anonapi_mock_cli.settings.servers) == 2
    runner.invoke(anonapi_mock_cli.main, ['server', 'remove', 'a_server'])

    assert len(anonapi_mock_cli.settings.servers) == 1

    # removing a non-existent server should not crash but yield nice message
    result = runner.invoke(anonapi_mock_cli.main, ['server', 'remove', 'non_existant_server'])
    assert result.exit_code == 1
    assert "Unknown server" in str(result.exception)



