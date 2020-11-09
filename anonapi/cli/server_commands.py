"""Click group and commands for the 'server' subcommand"""
import logging

import click

from anonapi.cli.click_parameter_types import AnonServerKeyParamType
from anonapi.context import AnonAPIContext, command_group_function
from anonapi.decorators import pass_anonapi_context
from anonapi.objects import RemoteAnonServer

logger = logging.getLogger(__name__)


@click.group(name="server")
def main():
    """Manage anonymization servers"""
    pass


@click.command()
@pass_anonapi_context
@click.argument("short_name", type=str)
@click.argument("url", type=str)
def add(context: AnonAPIContext, short_name, url):
    """Add a server to the list of servers in settings"""
    server = RemoteAnonServer(name=short_name, url=url)
    context.settings.servers.append(server)
    context.settings.save()
    logger.info(f"added {server} to list")


@command_group_function(name="list")
def server_list(context: AnonAPIContext):
    """Show all servers in settings"""
    servers = context.create_server_list()
    logger.info(f"Available servers (* = active):\n\n{servers}")


@click.command()
@pass_anonapi_context
@click.argument("short_name", metavar="SHORT_NAME", type=AnonServerKeyParamType())
def remove(context: AnonAPIContext, short_name):
    """Remove a server from list in settings"""
    server = context.get_server_by_name(short_name)
    if context.settings.active_server == server:
        # active server was removed, so it can no longer be active.
        context.settings.active_server = None

    context.settings.servers.remove(server)
    context.settings.save()
    logger.info(f"removed {server} from list")


@click.command()
@pass_anonapi_context
def status(context: AnonAPIContext):
    """Check whether active server is online and responding"""
    response = context.client_tool.get_server_status(context.get_active_server())
    logger.info(response)


@click.command()
@pass_anonapi_context
def jobs(context: AnonAPIContext):
    """List latest 100 jobs for active server"""
    response = context.client_tool.get_jobs(context.get_active_server())
    logger.info(response)


@click.command()
@pass_anonapi_context
@click.argument("short_name", metavar="SHORT_NAME", type=AnonServerKeyParamType())
def activate(context: AnonAPIContext, short_name):
    """Commands will use given server by default"""
    server = context.get_server_by_name(short_name)
    context.settings.active_server = server
    context.settings.save()
    logger.info(f"Set active server to {server}")


for func in [add, remove, server_list, status, jobs, activate]:
    main.add_command(func)
