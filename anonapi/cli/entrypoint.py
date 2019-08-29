"""Entrypoint for calling CLI with click.

"""
import pathlib

import click

from anonapi.cli import user_commands, parser, job_commands, batch_commands, map_commands, server_commands
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
    """\b
    anonymization web API tool
    Controls remote anonymization servers
    Use the commands below with -h for more info
    """
    ctx.obj = get_parser()


cli.add_command(parser.status)
cli.add_command(user_commands.main)
cli.add_command(job_commands.main)
cli.add_command(server_commands.main)
cli.add_command(batch_commands.main)
cli.add_command(map_commands.main)
