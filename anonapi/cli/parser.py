"""Command line utility object that gets passed around by click functions to have shared settings etc."""

import os
import click

from anonapi.batch import BatchFolder
from anonapi.client import AnonClientTool
from anonapi.objects import RemoteAnonServer
from anonapi.settings import AnonClientSettings


class AnonCommandLineParser:
    """Parses commands from commandline and launches actions accordingly.

    Tries to emulate command line structure used by git and docker: nested subcommands have their own help,
    certain data, like urls for web API servers, username, are persisted in settings file.

    """

    def __init__(self, client_tool: AnonClientTool, settings: AnonClientSettings):
        """Create a anonapi command line mock_context

        Parameters
        ----------
        client_tool: AnonClientTool
            The tool that that communicates with the web API.
        settings: AnonClientSettings
            Settings object to use for reading and writing settings.

        """
        self.client_tool = client_tool
        self.settings = settings

    # == Shared functions ===

    def create_server_list(self):
        server_list = ""
        for server in self.settings.servers:
            line = f"{server.name:<10} {server.url}"
            if server == self.settings.active_server:
                line = "* " + line
            else:
                line = "  " + line
            server_list += line + "\n"
        return server_list

    def get_server_by_name(self, short_name):
        """Get the server with given name from the list of servers

        Raises
        ------
        AnonCommandLineParserException:
            If server with that name cannot be found in list of servers

        """
        server_list = {x.name: x for x in self.settings.servers}
        if short_name not in server_list.keys():
            msg = f"Unknown server '{short_name}'. Please choose one of {[x.name for x in self.settings.servers]}"
            raise AnonCommandLineParserException(msg)

        return server_list[short_name]

    def get_active_server(self):
        """ Active server can be None, hence the check and exception

        Returns
        -------
        RemoteAnonServer
            The currently active server

        Raises
        ------
        AnonCommandLineParserException
            When there is no active server
        """
        server = self.settings.active_server
        if not server:
            msg = (
                f"No active server. Which one do you want to use? Please activate one by using 'server activate <SERVER_NAME>. "
                f"Available:{str([x.name for x in self.settings.servers])}"
            )
            raise AnonCommandLineParserException(msg)
        return server

    @staticmethod
    def current_dir():
        """Return full path to the folder this command line mock_context is called from"""
        return os.getcwd()

    def get_batch(self):
        """Get batch defined in current folder

        Raises
        ------
        NoBatchDefinedException

        Returns
        -------
        BatchFolder
        """

        batch = BatchFolder(self.current_dir()).load()
        if not batch:
            raise NoBatchDefinedException("No batch defined in current folder")
        else:
            return batch

    def get_batch_folder(self):
        """True if there is a batch defined in this folder"""
        return BatchFolder(self.current_dir())


def echo_error(msg):
    """Show this error message to user, but do not halt program flow

    Made this to have a consistent way to show error messages to user

    Parameters
    ----------
    msg: str
        Show this message

    """
    click.echo(f"Error: {msg}")


@click.command(short_help="show tool status")
@click.pass_obj
def status(parser: AnonCommandLineParser):
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


class AnonCommandLineParserException(Exception):
    pass


class NoBatchDefinedException(AnonCommandLineParserException):
    pass
