"""Command line utility object that gets passed around by click functions to have shared settings etc."""

import os
import click

from anonapi.batch import BatchFolder
from anonapi.client import WebAPIClient, APIClientException
from anonapi.objects import RemoteAnonServer
from anonapi.responses import (
    format_job_info_list,
    parse_job_infos_response,
    APIParseResponseException,
    JobsInfoList)
from anonapi.settings import (
    AnonClientSettings,
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
        """Create an API client with the information in this tool

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
        str:
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
        """Full description of a single job

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

    def get_job_info_list(self, server: RemoteAnonServer, job_ids):
        """Get a list of info on the given job ids. Info is shorter then full info

        Parameters
        ----------
        server: RemoteAnonServer
            get job info from this server
        job_ids: List[str]
            list of jobs to get info for

        Returns
        -------
        JobsInfoList:
            info describing each job. Info is omitted if job id could not be found

        Raises
        ------
        ClientToolException:
            if something goes wrong getting jobs info from server

        """
        client = self.get_client(server.url)
        try:
            return JobsInfoList(
                parse_job_infos_response(client.get("get_jobs_list", job_ids=job_ids))
            )
        except APIClientException as e:
            raise ClientToolException(f"Error getting jobs from {server}:\n{str(e)}")
        except APIParseResponseException as e:
            raise ClientToolException(
                f"Error parsing server response: from {server}:\n{str(e)}"
            )

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

        """
        job_limit = 50  # reduce number of jobs shown for less screen clutter.

        client = self.get_client(server.url)
        try:
            response_raw = client.get("get_jobs")
            response = parse_job_infos_response(response_raw)

            info_string = f"most recent {job_limit} jobs on {server.name}:\n\n"
            info_string += "\n" + format_job_info_list(response)
            return info_string

        except APIClientException as e:
            response = f"Error getting jobs from {server}:\n{str(e)}"
        except APIParseResponseException as e:
            response = f"Error parsing server response: from {server}:\n{str(e)}"

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

    Notes
    -----
    This class defines functions that in turn create click functions. For example get_server_commands(). This is
    a slightly underhanded way of using click function decorators but still being able to reference self.
    I have not found a better way though of keeping all code for this extensive CLI together while clearly referencing
    a single collection of settings.
    The current solution makes for a huge class. But the alternative would seem to be a huge unordered collection of
    flat functions.

    """

    def __init__(self, client_tool: AnonClientTool, settings: AnonClientSettings):
        """Create a anonapi command line parser

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
        """Return full path to the folder this command line parser is called from"""
        return os.getcwd()

    def get_batch(self):
        """Get batch defined in current folder"""

        batch = BatchFolder(self.current_dir()).load()
        if not batch:
            raise NoBatchDefinedException("No batch defined in current folder")
        else:
            return batch

    def get_batch_folder(self):
        """True if there is a batch defined in this folder"""
        return BatchFolder(self.current_dir())


@click.command(short_help='show tool status')
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


class MappingLoadException(AnonCommandLineParserException):
    pass


class ClientToolException(Exception):
    pass


