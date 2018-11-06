"""Command line utility for working with remote anonymization servers.

Modelled after command line interfaces of git and docker. Takes information from command line arguments but also saves
more permanent information in a settings file"""

import argparse
import random
import string
import sys
import pathlib
import os
import textwrap

from anonapi.client import WebAPIClient, APIClientException
from anonapi.objects import RemoteAnonServer
from anonapi.settings import (
    AnonClientSettings,
    DefaultAnonClientSettings,
    AnonClientSettingsFromFile,
)


class AnonClientTool:
    """Performs several actions via the Anonymization web API interface.

    One abstraction level above anonymization.client.WebAPIClient. Client deals with https calls, get and post,
    this tool should not do any http operations, and instead deal with servers and jobs.
    """

    def __init__(self, username, token):
        """Create an anonymization web API client tool

        Parameters
        ----------
        username: str
            use this when calling API
        token:
            API token to use when calling API

        """
        self.username = username
        self.token = token

    def get_client(self, url):
        """
        Returns
        -------
        WebAPIClient
        """
        client = WebAPIClient(hostname=url, username=self.username, token=self.token)
        return client

    def get_server_status(self, server: RemoteAnonServer):
        """

        Returns
        -------
        str
            status of the given server
        """
        client = self.get_client(server.url)
        try:
            client.get_documentation()  # don't care about documentation return value now, just using as test
            status = f"OK: {server} is online and responsive"
        except APIClientException as e:
            status = f"ERROR: {server} is not responding properly. Error:\n {str(e)}"

        return status

    def get_job_info(self, server: RemoteAnonServer, job_id: int):
        """

        Parameters
        ----------
        server: :obj:`RemoteAnonServer`
            get job info from this server
        job_id: str
            id of job to get info for


        Returns
        -------
        str:
            string describing job, or error if job could not be found

        """

        client = self.get_client(server.url)

        try:
            response = client.get("get_job", job_id=job_id)
            info_string = f"job {job_id} on {server.name}:\n\n"
            info_string += "\n".join([str(x) for x in list(response.items())])

        except APIClientException as e:
            info_string = f"Error getting job info from {server}:\n{str(e)}"
        return info_string

    def get_jobs(self, server: RemoteAnonServer):
        """Get list of info on most recent jobs in server

        Parameters
        ----------
        server: :obj:`RemoteAnonServer`
            get job info from this server

        Returns
        -------
        str:
            string describing job, or error if job could not be found

        Raises
        ------
        APIClientException:
            if something goes wrong getting jobs info from server

        """
        job_limit = 50  # reduce number of jobs shown for less screen clutter.

        client = self.get_client(server.url)
        try:
            response = client.get("get_jobs")
            info_string = f"most recent {job_limit} jobs on {server.name}:\n\n"

            header = (
                "id     date                 status   downloaded processed  user\n"
                "---------------------------------------------------------------"
            )
            info_string += "\n" + header
            job_infos = list(response.values())
            job_infos = job_infos[
                :job_limit
            ]  # reduce number of jobs shown for less screen clutter.
            for job_info in job_infos:
                x = job_info
                info_line = (
                    f"{x['job_id']:<6} {x['date']:<20} {x['status']:<8} {str(x['files_downloaded']):<10} "
                    f"{str(x['files_processed']):<10} {x['user_name']}"
                )
                info_string += "\n" + info_line
            return info_string

        except APIClientException as e:
            response = f"Error getting jobs from {server}:\n{str(e)}"
        return response

    def cancel_job(self, server: RemoteAnonServer, job_id: int):
        """Cancel the given job

        Returns
        -------
        str
            a string describing success or any API error
        """
        client = self.get_client(server.url)
        try:
            _ = client.post("cancel_job", job_id=job_id)
            info = f"Cancelled job {job_id} on {server.name}"
        except APIClientException as e:
            info = f"Error cancelling job on{server}:\n{str(e)}"
        return info

    def reset_job(self, server, job_id):
        """Reset job status, error and downloaded/processed counters

        Returns
        -------
        str
            a string describing success or any API error
        """

        client = self.get_client(server.url)
        try:
            _ = client.post(
                "modify_job",
                job_id=job_id,
                status="ACTIVE",
                files_downloaded=0,
                files_processed=0,
                error=" ",
            )
            info = f"Reset job {job_id} on {server}"
        except APIClientException as e:
            info = f"Error resetting job on{server.name}:\n{str(e)}"
        return info

        pass


class AnonCommandLineParser:
    """Parses commands from commandline and launches actions accordingly.

    Tries to emulate command line structure used by git and docker: nested subcommands have their own help,
    certain data, like urls for web API servers, username, are persisted in settings file.

    """

    def __init__(self, client_tool: AnonClientTool, settings: AnonClientSettings):
        """Create a command line parser

        Parameters
        ----------
        client_tool: :obj:`AnonClientTool`
            The tool that that communicates with the web API.
        settings: :obj:`AnonClientSettings`
            Settings object to use for reading and writing settings.

        """
        self.client_tool = client_tool
        self.settings = settings
        self.parser = self.create_parser()

    def create_parser(self):
        """The thing that actually parses the input commands.

        Notes
        -----
        Uses subparsers and the set_defaults(func=foo()) trick to link functions to each subparser. func is later
        passed along at each parse and later executed in execute_command()

        """
        # create the top-level parser
        parser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description=textwrap.dedent(
                """
                anonymization web API tool
                Controls remote anonymization servers via the anonymization web API       
                Use the commands below with -h for more info
            """
            ),
        )
        parser.set_defaults(func=lambda: parser.print_help())
        subparsers = parser.add_subparsers()

        # ============================================================================================
        status_parser = subparsers.add_parser(
            "status",
            help="show tool status",
            description="show overview of this tool's status",
        )
        status_parser.set_defaults(func=self.get_status)

        # ============================================================================================
        server_parser = subparsers.add_parser(
            "server",
            help="manage anonymization servers",
            description="manage anonymization servers",
        )
        self.add_server_actions(parser=server_parser)

        # ============================================================================================
        job_parser = subparsers.add_parser(
            "job",
            help="manage anonymization jobs",
            description="manage anonymization jobs on active server",
        )
        self.add_job_actions(parser=job_parser)

        # ============================================================================================
        user_parser = subparsers.add_parser(
            "user",
            help="manage API credentials",
            description="manage username and API key",
        )
        self.add_user_actions(parser=user_parser)

        return parser

    def add_server_actions(self, parser):
        parser.set_defaults(func=lambda: parser.print_help())
        parser_sub = parser.add_subparsers()

        parser_add = parser_sub.add_parser(
            "add",
            help="add a server",
            description="add an anonymization server to the list of servers",
        )
        parser_add.add_argument(
            "short_name", type=str, help="short name to use in commands"
        )
        parser_add.add_argument(
            "url", type=str, help="full path including https:// to server"
        )
        parser_add.set_defaults(func=self.server_add)

        parser_remove = parser_sub.add_parser(
            "remove",
            help="remove a server",
            description="remove a server from list of servers",
        )
        parser_remove.add_argument(
            "short_name", type=str, help="short name of server to remove"
        )
        parser_remove.set_defaults(func=self.server_remove)

        parser_add = parser_sub.add_parser(
            "list", help="list anon servers", description="list anon servers"
        )
        parser_add.set_defaults(func=self.server_list)

        parser_status = parser_sub.add_parser(
            "status",
            help="get status of active server",
            description="get status of active server, or given server",
        )
        parser_status.add_argument(
            "short_name",
            nargs="?",
            type=str,
            help="optional short name of server to show status for. Defaults to active server",
        )
        parser_status.set_defaults(func=self.server_status)

        parser_jobs = parser_sub.add_parser(
            "jobs", help="list latest 50 jobs", description="list latest 50 jobs"
        )
        parser_jobs.add_argument(
            "short_name",
            nargs="?",
            type=str,
            help="optional short name of server to list jobs for. Defaults to active server",
        )
        parser_jobs.set_defaults(func=self.server_jobs)

        parser_activate = parser_sub.add_parser(
            "activate",
            help="set active server",
            description="set given server as active. Commands that require a server"
            " will use this server by default from now on",
        )
        parser_activate.add_argument(
            "short_name", type=str, help="short name of server to activate"
        )
        parser_activate.set_defaults(func=self.server_activate)

    def add_job_actions(self, parser):
        parser.set_defaults(func=lambda: parser.print_help())
        parser_sub = parser.add_subparsers()

        parser_info = parser_sub.add_parser(
            "info",
            help="print job info",
            description="query the active server to retrieve info for this job",
        )
        parser_info.add_argument("job_id", type=int, help="Job id to check")
        parser_info.set_defaults(func=self.get_job_info)

        parser_restart = parser_sub.add_parser(
            "reset",
            help="reset job, process again",
            description="reset job, process again",
        )
        parser_restart.add_argument("job_id", type=int, help="Job id to reset")
        parser_restart.set_defaults(func=self.job_reset)

        parser_cancel = parser_sub.add_parser(
            "cancel", help="sets job status to inactive", description="cancel job"
        )
        parser_cancel.add_argument("job_id", type=int, help="Job id to cancel")
        parser_cancel.set_defaults(func=self.job_cancel)

    def add_user_actions(self, parser):
        parser.set_defaults(func=lambda: parser.print_help())
        parser_sub = parser.add_subparsers()

        parser_info = parser_sub.add_parser(
            "info",
            help="print current credentials",
            description="print current credentials",
        )
        parser_info.set_defaults(func=self.user_info)

        parser_username = parser_sub.add_parser(
            "set_username", help="set username", description="print job info"
        )
        parser_username.add_argument("user_name", type=str, help="set username to this")
        parser_username.set_defaults(func=self.set_username)

        parser_get_api_token = parser_sub.add_parser(
            "get_token",
            help="retrieve an API token for the current user. "
            "Requires valid UMCN credentials",
            description="retrieve an api token for the current user. "
            "Requires valid UMCN credentials",
        )
        parser_get_api_token.set_defaults(func=self.get_token)

    def get_status(self):
        """Get general status of this tool, show currently active server etc.

        Returns
        -------
        str
        """
        server_list = self.create_server_list()
        status = (
            f"Available servers (* = active)\n\n"
            f"{server_list}\n"
            f"Using username: '{self.settings.user_name}'\n"
            f"Reading settings from \n"
            f"{self.settings}"
        )

        self.print_to_console(status)

    def server_add(self, short_name, url):
        """Add a server to the list of servers in settings """

        server = RemoteAnonServer(name=short_name, url=url)
        self.settings.servers.append(server)
        self.settings.save()
        self.print_to_console(f"added {server} to list")

    def server_list(self):
        """show all servers in settings """
        server_list = self.create_server_list()
        self.print_to_console(f"Available servers (* = active):\n\n{server_list}")

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

    def server_remove(self, short_name):
        """Remove a servers from list in settings"""
        server = self.get_server_by_name(short_name)
        if self.settings.active_server == server:
            # active server was removed, so it can no longer be active.
            self.settings.active_server = None

        self.settings.servers.remove(server)
        self.settings.save()
        self.print_to_console(f"removed {server} from list")

    def server_status(self, short_name=None):
        """Check whether active server is online and responding like an anonymization web API, optionaly check given
        server instead of active
        """

        server = self.get_server_or_active_server(short_name)
        response = self.client_tool.get_server_status(server)
        self.print_to_console(str(response))

    def server_jobs(self, short_name=None):
        """List latest 100 jobs for active server, or given server
        """
        server = self.get_server_or_active_server(short_name)
        response = self.client_tool.get_jobs(server)
        self.print_to_console(response)

    def server_activate(self, short_name):
        """Set given server as activate server, meaning subsequent operations will use this server.
        """
        server = self.get_server_by_name(short_name)
        self.settings.active_server = server
        self.settings.save()
        self.print_to_console(f"Set active server to {server}")

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

    def get_job_info(self, job_id):
        """ Query active server for info on this job
        """
        server = self.get_active_server()
        info = self.client_tool.get_job_info(server=server, job_id=job_id)
        self.print_to_console(info)

    def job_reset(self, job_id):
        server = self.get_active_server()
        info = self.client_tool.reset_job(server=server, job_id=job_id)
        self.print_to_console(info)

    def job_cancel(self, job_id):
        server = self.get_active_server()
        info = self.client_tool.cancel_job(server=server, job_id=job_id)
        self.print_to_console(info)

    def get_server_or_active_server(self, short_name=None):
        """Return server corresponding to short_name, or active server"""
        if short_name:
            server = self.get_server_by_name(short_name)
        else:
            server = self.get_active_server()
        return server

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
                f"No active server. Which one do you want to use? Please activate one by using 'server activate <servername>. "
                f"Available:{str([x.name for x in self.settings.servers])}"
            )
            raise AnonCommandLineParserException(msg)
        return server

    def user_info(self):
        self.print_to_console(
            f"username is {self.settings.user_name}\nAPI token: {self.settings.user_token}"
        )

    def set_username(self, user_name):
        """Set the given username in settings

        Parameters
        ----------
        user_name: str
            set this username

        """
        self.settings.user_name = user_name
        self.settings.save()
        self.print_to_console(f"username is now '{user_name}'")

    def get_token(self):
        token = "".join(
            random.SystemRandom().choice(
                string.ascii_uppercase + string.ascii_lowercase + string.digits
            )
            for _ in range(64)
        )
        self.settings.user_token = token
        self.settings.save()
        self.print_to_console(
            f"Got and saved api token for username {self.settings.user_name}"
        )

    @staticmethod
    def print_to_console(msg):
        """Print this message to console. With minimal formatting.

        Parameters
        ----------
        msg: str

        """
        # indent text so it is more visible
        lines = msg.split("\n")
        indented = "\n" + "\n".join(["  " + line for line in lines])
        print(indented)

    def execute_command(self, cmd):
        """Parse command line string and execute functions accordingly

        Parameters
        ----------
        cmd

        Notes
        -----
        the result of parser.parse_args() always contains the key 'func' because it is explicitly added for each
        parser in self.create_parser() See that that method's doc string notes for more info.

        """
        args = self.parser.parse_args(cmd)
        args_dict = vars(args)
        func = args_dict.pop("func")
        try:
            func(**args_dict)
        except AnonCommandLineParserException as e:
            self.print_to_console(str(e))


class AnonCommandLineParserException(Exception):
    pass


def main():
    global settings_file
    settings_file = pathlib.Path.home() / "AnonWebAPIClientSettings.yml"
    if not os.path.exists(settings_file):
        print(f"Settings file did not exist. creating '{settings_file}'")
        DefaultAnonClientSettings().save_to_file(filename=settings_file)
    settings = AnonClientSettingsFromFile(settings_file)
    tool = AnonClientTool(username=settings.user_name, token=settings.user_token)
    parser = AnonCommandLineParser(client_tool=tool, settings=settings)
    parser.execute_command(sys.argv[1:])


if __name__ == "__main__":
    main()
