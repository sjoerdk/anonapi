import os
from pathlib import Path

from anonapi.batch import BatchFolder
from anonapi.client import AnonClientTool
from anonapi.exceptions import AnonAPIException
from anonapi.settings import AnonClientSettings


class AnonAPIContext:
    """Base context passed to all anonapi commands. Contains settings and connection
    to the API

    """

    def __init__(
        self,
        client_tool: AnonClientTool,
        settings: AnonClientSettings,
        current_dir: Path = None,
    ):
        """Create a anonapi command line mock_context

        Parameters
        ----------
        client_tool: AnonClientTool
            The tool that that communicates with the web API.
        settings: AnonClientSettings
            Settings object to use for reading and writing settings.
        current_dir: Path, optional
            Full root_path to the directory that anonapi is being called from. Defaults
            to None

        """
        self.client_tool = client_tool
        self.settings = settings
        self.current_dir = current_dir

    def create_server_list(self):
        """ A concise, printable overview of servers

        Returns
        -------
        str:
            A concise, printable overview of servers

        """
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
        AnonAPIContextException:
            If server with that name cannot be found in list of servers

        Returns
        -------
        RemoteAnonServer
            The server with the given name
        """
        server_list = {x.name: x for x in self.settings.servers}
        if short_name not in server_list.keys():
            msg = f"Unknown server '{short_name}'. Please choose one of {[x.name for x in self.settings.servers]}"
            raise AnonAPIContextException(msg)

        return server_list[short_name]

    def get_active_server(self):
        """ Active server can be None, hence the check and exception

        Returns
        -------
        RemoteAnonServer
            The currently active server

        Raises
        ------
        AnonAPIContextException
            When there is no active server
        """
        server = self.settings.active_server
        if not server:
            msg = (
                f"No active server. Which one do you want to use? Please activate "
                f"one by using 'server activate <SERVER_NAME>. "
                f"Available:{str([x.name for x in self.settings.servers])}"
            )
            raise AnonAPIContextException(msg)
        return server

    def current_dir(self):
        """Return full root_path to the folder this command line mock_context is
        called from"""
        return self.current_dir

    def get_batch(self):
        """Get batch defined in current folder

        Raises
        ------
        NoBatchDefinedException

        Returns
        -------
        JobBatch
        """

        batch = BatchFolder(self.current_dir).load()
        if not batch:
            raise NoBatchDefinedException("No batch defined in current folder")
        else:
            return batch

    def get_batch_folder(self):
        """True if there is a batch defined in this folder"""
        return BatchFolder(self.current_dir)


class AnonAPIContextException(AnonAPIException):
    pass


class NoBatchDefinedException(AnonAPIContextException):
    pass
