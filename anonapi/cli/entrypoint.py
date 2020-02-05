"""Entrypoint for calling CLI with click.

"""
import os
import pathlib

import click

from anonapi.cli import (
    user_commands,
    parser,
    job_commands,
    batch_commands,
    map_commands,
    server_commands,
    select_commands,
    create_commands,
    settings_commands,
)
from anonapi.context import AnonAPIContext
from anonapi.client import AnonClientTool
from anonapi.settings import AnonClientSettingsFromFile, DefaultAnonClientSettings


def get_context():
    """Create a default mock_context instance

    Returns
    -------
    AnonAPIContext
    """

    settings_file = pathlib.Path.home() / "AnonWebAPIClientSettings.yml"
    if not settings_file.exists():
        click.echo(
            f'No settings file found. Creating default settings at "{settings_file}"'
        )
        DefaultAnonClientSettings().save_to_file(settings_file)
    settings = AnonClientSettingsFromFile(settings_file)
    tool = AnonClientTool(username=settings.user_name, token=settings.user_token)
    parser = AnonAPIContext(
        client_tool=tool, settings=settings, current_dir=os.getcwd()
    )
    return parser


@click.group()
@click.pass_context
def cli(ctx):
    """\b
    anonymization web API tool
    Controls remote anonymization servers
    Use the commands below with -h for more info
    """
    ctx.obj = get_context()


cli.add_command(parser.status)
cli.add_command(job_commands.main)
cli.add_command(server_commands.main)
cli.add_command(batch_commands.main)
cli.add_command(map_commands.main)
cli.add_command(select_commands.main)
cli.add_command(create_commands.main)
cli.add_command(settings_commands.main)
