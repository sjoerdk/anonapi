"""Entrypoint for calling CLI with click.

"""
import pathlib

import click

from anonapi.cli import user_functions
from anonapi.cli.parser import AnonClientTool, AnonCommandLineParser
from anonapi.settings import AnonClientSettingsFromFile


def get_parser():
    """Create a default parser instance
    """

    settings_file = pathlib.Path.home() / "AnonWebAPIClientSettings.yml"
    settings = AnonClientSettingsFromFile(settings_file)
    tool = AnonClientTool(username=settings.user_name, token=settings.user_token)
    parser = AnonCommandLineParser(client_tool=tool, settings=settings)
    return parser


@click.group()
@click.pass_context
def cli(ctx):
    ctx.obj = get_parser()


cli.add_command(user_functions.main)
