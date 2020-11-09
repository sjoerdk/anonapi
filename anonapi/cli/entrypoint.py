"""Entrypoint for calling CLI with click."""
import locale
import logging
import os
from pathlib import Path

import click

from anonapi.cli import (
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
from anonapi.logging import AnonAPILogController, Verbosities
from anonapi.persistence import DEFAULT_SETTINGS_PATH
from anonapi.settings import DefaultAnonClientSettings, AnonClientSettingsFromFile

logger = logging.getLogger(__name__)


def get_settings_path() -> Path:
    """Separate method for easier spoofing during tests"""
    return DEFAULT_SETTINGS_PATH


def get_settings() -> AnonClientSettingsFromFile:
    """Obtain local anonapi settings. Creates default settings file if not found"""
    settings_file = get_settings_path()
    if not settings_file.exists():
        logger.info(
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
@click.option("-v", "--verbose", count=True)
@click.pass_context
def cli(ctx, verbose):
    r"""\b
    anonymization web API tool
    Controls remote anonymization servers
    Use the commands below with -h for more info
    """
    locale.setlocale(locale.LC_ALL, "")  # use local instead of default 'C' locale
    configure_logging(verbose)
    ctx.obj = get_context()


def configure_logging(verbose):
    log_controller = AnonAPILogController(
        logger=logging.getLogger()
    )  # control root logger
    if verbose == 0:
        log_controller.set_verbosity(Verbosities.TERSE)
    elif verbose == 1:
        log_controller.set_verbosity(Verbosities.VERBOSE)
    elif verbose >= 2:
        log_controller.set_verbosity(Verbosities.VERY_VERBOSE)


@click.command(short_help="show tool status")
@click.pass_obj
def status(context: AnonAPIContext):
    """Get general status of this tool, show currently active server etc."""
    logger.info("Status")
    server_list = context.create_server_list()
    status = (
        f"Available servers (* = active)\n\n"
        f"{server_list}\n"
        f"Using username: '{context.settings.user_name}'\n"
        f"Reading settings from \n"
        f"{context.settings}"
    )
    logger.info(status)


cli.add_command(status)
cli.add_command(job_commands.main)
cli.add_command(server_commands.main)
cli.add_command(batch_commands.main)
cli.add_command(map_commands.main)
cli.add_command(select_commands.main)
cli.add_command(create_commands.main)
cli.add_command(settings_commands.main)
