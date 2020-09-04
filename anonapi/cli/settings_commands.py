"""User sub commands"""


import click

from anonapi.cli import user_commands
from anonapi.context import AnonAPIContext
from anonapi.decorators import pass_anonapi_context


@click.group(name="settings")
def main():
    """Manage local settings"""
    pass


@click.command()
@pass_anonapi_context
@click.argument("value", type=bool)
def set_validate_ssl(parser: AnonAPIContext, value: bool):
    """If False, ignore all ssl certificate errors"""
    parser.settings.validate_ssl = value
    parser.settings.save()
    click.echo(f"Set validate ssl to {value}")


@click.command()
@pass_anonapi_context
def show(parser: AnonAPIContext):
    """Show all settings"""
    click.echo(parser.settings.as_human_readable())


main.add_command(user_commands.main)
main.add_command(set_validate_ssl)
main.add_command(show)
