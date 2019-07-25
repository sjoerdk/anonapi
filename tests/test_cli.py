#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pytest import fixture
from click.testing import CliRunner

from anonapi.cli import AnonClientTool, AnonCommandLineParser
from anonapi.objects import RemoteAnonServer
from anonapi.settings import AnonClientSettings


@fixture
def anonapi_mock_cli():
    """Returns click entrypoint for a mock AnonCommandLineParser

    """
    settings = AnonClientSettings(servers=[RemoteAnonServer(name='testserver', url='https://testurl')],
                                  user_name='testuser',
                                  user_token='testtoken')
    tool = AnonClientTool(username=settings.user_name, token=settings.user_token)
    return AnonCommandLineParser(client_tool=tool, settings=settings).main


def test_command_line_tool_basic(anonapi_mock_cli):
    """Test most basic invocation"""

    runner = CliRunner()
    result = runner.invoke(anonapi_mock_cli)
    assert result.exit_code == 0
    assert "anonymization web API tool" in result.stdout
