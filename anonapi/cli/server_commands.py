"""Click group and commands for the 'server' subcommand
"""
import click

from anonapi.cli.click_types import AnonServerKeyParamType
from anonapi.cli.parser import AnonCommandLineParser, command_group_function
from anonapi.objects import RemoteAnonServer


@click.group(name="server")
def main():
    """manage anonymization servers"""
    pass


@command_group_function()
@click.argument("short_name", type=str)
@click.argument("url", type=str)
def add(parser: AnonCommandLineParser, short_name, url):
    """Add a server to the list of servers in settings """
    server = RemoteAnonServer(name=short_name, url=url)
    parser.settings.servers.append(server)
    parser.settings.save()
    click.echo(f"added {server} to list")


@command_group_function(name="list")
def server_list(parser: AnonCommandLineParser):
    """show all servers in settings """
    servers = parser.create_server_list()
    click.echo(f"Available servers (* = active):\n\n{servers}")


@command_group_function()
@click.argument("short_name", metavar="SHORT_NAME", type=AnonServerKeyParamType())
def remove(parser: AnonCommandLineParser, short_name):
    """Remove a server from list in settings"""
    server = parser.get_server_by_name(short_name)
    if parser.settings.active_server == server:
        # active server was removed, so it can no longer be active.
        parser.settings.active_server = None

    parser.settings.servers.remove(server)
    parser.settings.save()
    click.echo(f"removed {server} from list")


@command_group_function()
def status(parser: AnonCommandLineParser):
    """Check whether active server is online and responding like an anonymization web API, optionaly check given
    server instead of active
    """
    response = parser.client_tool.get_server_status(parser.get_active_server())
    click.echo(response)


@command_group_function()
def jobs(parser: AnonCommandLineParser):
    """List latest 100 jobs for active server, or given server
    """
    response = parser.client_tool.get_jobs(parser.get_active_server())
    click.echo(response)


@command_group_function()
@click.argument("short_name", metavar="SHORT_NAME", type=AnonServerKeyParamType())
def activate(parser: AnonCommandLineParser, short_name):
    """Set given server as activate server, meaning subsequent operations will use this server.
    """
    server = parser.get_server_by_name(short_name)
    parser.settings.active_server = server
    parser.settings.save()
    click.echo(f"Set active server to {server}")


for func in [add, remove, server_list, status, jobs, activate]:
    main.add_command(func)
