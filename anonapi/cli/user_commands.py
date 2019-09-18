"""User sub commands

"""
import random
import string

import click

from anonapi.cli.parser import AnonCommandLineParser, command_group_function


@click.group(name="user")
def main():
    """manage API credentials"""


@command_group_function()
def info(parser: AnonCommandLineParser):
    """show current credentials"""
    click.echo(
        f"username is {parser.settings.user_name}\nAPI token: {parser.settings.user_token}"
    )


@command_group_function()
@click.argument("user_name", type=str)
def set_username(parser: AnonCommandLineParser, user_name):
    """Set the given username in settings
    """
    parser.settings.user_name = user_name
    parser.settings.save()
    click.echo(f"username is now '{user_name}'")


@command_group_function()
def get_token(parser: AnonCommandLineParser):
    """Obtain a security token
    """
    token = "".join(
        random.SystemRandom().choice(
            string.ascii_uppercase + string.ascii_lowercase + string.digits
        )
        for _ in range(64)
    )
    parser.settings.user_token = token
    parser.settings.save()
    click.echo(f"Got and saved api token for username {parser.settings.user_name}")


for func in [info, set_username, get_token]:
    main.add_command(func)
