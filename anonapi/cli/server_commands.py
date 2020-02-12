"""Click group and commands for the 'server' subcommand
"""
import click

from anonapi.cli.click_types import AnonServerKeyParamType
from anonapi.cli.parser import command_group_function
from anonapi.context import AnonAPIContext
from anonapi.decorators import pass_anonapi_context
from anonapi.objects import RemoteAnonServer


@click.group(name="server")
def main():
    """manage anonymization servers"""
    pass


@click.command()
@pass_anonapi_context
@click.argument("short_name", type=str)
@click.argument("url", type=str)
def add(parser: AnonAPIContext, short_name, url):
    """Add a server to the list of servers in settings """
    server = RemoteAnonServer(name=short_name, url=url)
    parser.settings.servers.append(server)
    parser.settings.save()
    click.echo(f"added {server} to list")


@command_group_function(name="list")
def server_list(parser: AnonAPIContext):
    """show all servers in settings """
    servers = parser.create_server_list()
    click.echo(f"Available servers (* = active):\n\n{servers}")


@click.command()
@pass_anonapi_context
@click.argument("short_name", metavar="SHORT_NAME", type=AnonServerKeyParamType())
def remove(parser: AnonAPIContext, short_name):
    """Remove a server from list in settings"""
    server = parser.get_server_by_name(short_name)
    if parser.settings.active_server == server:
        # active server was removed, so it can no longer be active.
        parser.settings.active_server = None

    parser.settings.servers.remove(server)
    parser.settings.save()
    click.echo(f"removed {server} from list")


@click.command()
@pass_anonapi_context
def status(parser: AnonAPIContext):
    """Check whether active server is online and responding
    """
    response = parser.client_tool.get_server_status(parser.get_active_server())
    click.echo(response)


@click.command()
@pass_anonapi_context
def jobs(parser: AnonAPIContext):
    """List latest 100 jobs for active server
    """
    response = parser.client_tool.get_jobs(parser.get_active_server())
    click.echo(response)


@click.command()
@pass_anonapi_context
@click.argument("short_name", metavar="SHORT_NAME", type=AnonServerKeyParamType())
def activate(parser: AnonAPIContext, short_name):
    """Commands will use given server by default
    """
    server = parser.get_server_by_name(short_name)
    parser.settings.active_server = server
    parser.settings.save()
    click.echo(f"Set active server to {server}")


for func in [add, remove, server_list, status, jobs, activate]:
    main.add_command(func)
