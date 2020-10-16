"""User sub commands"""
import logging
import random
import string

import click

from anonapi.context import AnonAPIContext
from anonapi.decorators import pass_anonapi_context


logger = logging.getLogger(__name__)


@click.group(name="user")
def main():
    """Manage API credentials"""


@click.command()
@pass_anonapi_context
def info(context: AnonAPIContext):
    """Show current credentials"""
    logger.info(
        f"username is {context.settings.user_name}\nAPI token: {context.settings.user_token}"
    )


@click.command()
@pass_anonapi_context
@click.argument("user_name", type=str)
def set_username(context: AnonAPIContext, user_name):
    """Set the given username in settings"""
    context.settings.user_name = user_name
    context.settings.save()
    logger.info(f"username is now '{user_name}'")


@click.command()
@pass_anonapi_context
def get_token(context: AnonAPIContext):
    """Obtain a security token"""
    token = "".join(
        random.SystemRandom().choice(
            string.ascii_uppercase + string.ascii_lowercase + string.digits
        )
        for _ in range(64)
    )
    context.settings.user_token = token
    context.settings.save()
    logger.info(f"Got and saved api token for username {context.settings.user_name}")


for func in [info, set_username, get_token]:
    main.add_command(func)
