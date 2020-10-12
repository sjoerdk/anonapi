"""User sub commands"""
import logging

import click

from anonapi.cli import user_commands
from anonapi.context import AnonAPIContext
from anonapi.decorators import pass_anonapi_context


logger = logging.getLogger(__name__)


@click.group(name="settings")
def main():
    """Manage local settings"""
    pass


@click.command()
@pass_anonapi_context
@click.argument("value", type=bool)
def set_validate_ssl(context: AnonAPIContext, value: bool):
    """If False, ignore all ssl certificate errors"""
    context.settings.validate_ssl = value
    context.settings.save_to()
    logger.info(f"Set validate ssl to {value}")


@click.command()
@pass_anonapi_context
def show(context: AnonAPIContext):
    """Show all settings"""
    logger.info(context.settings.as_human_readable())


main.add_command(user_commands.main)
main.add_command(set_validate_ssl)
main.add_command(show)
