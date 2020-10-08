"""Entrypoint for calling CLI with click."""
import locale
import os

import click

from anonapi.cli import (
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
from anonapi.persistence import DEFAULT_SETTINGS_PATH
from anonapi.settings import DefaultAnonClientSettings, AnonClientSettingsFromFile


def get_settings_path() -> str:
    """Separate method for easier spoofing during tests"""
    return DEFAULT_SETTINGS_PATH


def get_settings() -> AnonClientSettingsFromFile:
    """Obtain local anonapi settings. Creates default settings file if not found"""
    settings_file = get_settings_path()
    if not settings_file.exists():
        click.echo(
            f'No settings file found. Creating default settings at "{settings_file}"'
        )
        with open(settings_file, "w") as f:
            DefaultAnonClientSettings().save_to(f)

    return AnonClientSettingsFromFile(path=settings_file)


def get_context() -> AnonAPIContext:
    """Collect all info used by all anonapi commands. Settings, current dir, etc.

    Returns
    -------
    AnonAPIContext
    """

    settings = get_settings()
    tool = AnonClientTool(
        username=settings.user_name,
        token=settings.user_token,
        validate_https=settings.validate_ssl,
    )
    context = AnonAPIContext(
        client_tool=tool, settings=settings, current_dir=os.getcwd()
    )
    return context


@click.group()
@click.pass_context
def cli(ctx):
    r"""\b
    anonymization web API tool
    Controls remote anonymization servers
    Use the commands below with -h for more info
    """
    locale.setlocale(locale.LC_ALL, "")  # use local instead of default 'C' locale
    ctx.obj = get_context()


cli.add_command(parser.status)
cli.add_command(job_commands.main)
cli.add_command(server_commands.main)
cli.add_command(batch_commands.main)
cli.add_command(map_commands.main)
cli.add_command(select_commands.main)
cli.add_command(create_commands.main)
cli.add_command(settings_commands.main)
