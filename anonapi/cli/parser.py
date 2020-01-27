"""Command line utility object that gets passed around by click functions to
have shared settings etc."""

import click

from anonapi.context import AnonAPIContext


@click.command(short_help="show tool status")
@click.pass_obj
def status(parser: AnonAPIContext):
    """Get general status of this tool, show currently active server etc."""
    click.echo("Status is really good")
    server_list = parser.create_server_list()
    status = (
        f"Available servers (* = active)\n\n"
        f"{server_list}\n"
        f"Using username: '{parser.settings.user_name}'\n"
        f"Reading settings from \n"
        f"{parser.settings}"
    )
    click.echo(status)


def command_group_function(**kwargs):
    """Combines decorators used for all click functions inside a ClickCommandGroup
    Identical to

    @click.command(**kwargs)
    @click.pass_obj

    Just to prevent duplicated code
    """

    def decorator(func):
        return click.command(**kwargs)((click.pass_obj(func)))

    return decorator
