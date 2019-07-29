"""Command line utility for working with remote anonymization servers.

Modelled after command line interfaces of git and docker. Takes information from command line arguments but also saves
more permanent information in a settings file"""
import itertools
import os
import random
import string

import click

from anonapi.batch import JobBatch, BatchFolder
from anonapi.click_types import JobIDRangeParamType
from anonapi.client import WebAPIClient, APIClientException
from anonapi.objects import RemoteAnonServer
from anonapi.responses import (
    format_job_info_list,
    parse_job_infos_response,
    APIParseResponseException,
    JobsInfoList, JobStatus)
from anonapi.settings import (
    AnonClientSettings,
)
from collections import Counter


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
        """Create a command line parser

        Parameters
        ----------
        client_tool: AnonClientTool
            The tool that that communicates with the web API.
        settings: AnonClientSettings
            Settings object to use for reading and writing settings.

        """
        self.client_tool = client_tool
        self.settings = settings

        self.main.add_command(self.get_status_command())
        self.main.add_command(self.get_server_commands())
        self.main.add_command(self.get_job_commands())
        self.main.add_command(self.get_user_commands())
        self.main.add_command(self.get_batch_commands())

    @staticmethod
    @click.group()
    def main():
        """\b
        anonymization web API tool
        Controls remote anonymization servers
        Use the commands below with -h for more info
        """
        pass

    def get_status_command(self):
        """click command for the 'status' subcommand """

        @click.command(short_help='show tool status')
        def status():
            """Get general status of this tool, show currently active server etc."""
            click.echo("Status is really good")
            server_list = self.create_server_list()
            status = (
                f"Available servers (* = active)\n\n"
                f"{server_list}\n"
                f"Using username: '{self.settings.user_name}'\n"
                f"Reading settings from \n"
                f"{self.settings}"
            )
            click.echo(status)
        return status

    def get_server_commands(self):
        """Click group and commands for the 'server' subcommand

        """

        def get_server_list():
            """Specifies a list of all currently defined API server"""
            return click.Choice([x.name for x in self.settings.servers])

        @click.group()
        def server():
            """manage anonymization servers"""
            pass

        @click.command()
        @click.argument('short_name', type=str)
        @click.argument('url', type=str)
        def add(short_name, url):
            """Add a server to the list of servers in settings """
            server = RemoteAnonServer(name=short_name, url=url)
            self.settings.servers.append(server)
            self.settings.save()
            click.echo(f"added {server} to list")

        @click.command('list')
        def server_list():
            """show all servers in settings """
            servers = self.create_server_list()
            click.echo(f"Available servers (* = active):\n\n{servers}")

        @click.command()
        @click.argument('short_name', metavar='SHORT_NAME', type=get_server_list())
        def remove(short_name):
            """Remove a server from list in settings"""
            server = self.get_server_by_name(short_name)
            if self.settings.active_server == server:
                # active server was removed, so it can no longer be active.
                self.settings.active_server = None

            self.settings.servers.remove(server)
            self.settings.save()
            click.echo(f"removed {server} from list")

        @click.command()
        def status():
            """Check whether active server is online and responding like an anonymization web API, optionaly check given
            server instead of active
            """
            response = self.client_tool.get_server_status(self.get_active_server())
            click.echo(response)

        @click.command()
        def jobs():
            """List latest 100 jobs for active server, or given server
            """
            response = self.client_tool.get_jobs(self.get_active_server())
            click.echo(response)

        @click.command()
        @click.argument('short_name', metavar='SHORT_NAME', type=get_server_list())
        def activate(short_name):
            """Set given server as activate server, meaning subsequent operations will use this server.
            """
            server = self.get_server_by_name(short_name)
            self.settings.active_server = server
            self.settings.save()
            click.echo(f"Set active server to {server}")

        for func in [add, remove, server_list, status, jobs, activate]:
            server.add_command(func)
        return server

    def get_job_commands(self):
        """Click group and commands for the 'job' subcommand

        """

        @click.group()
        def job():
            """manage anonymization jobs"""
            pass

        @click.command()
        @click.argument('job_id', type=str)
        def info(job_id):
            """print job info
            """
            server = self.get_active_server()
            job_info = self.client_tool.get_job_info(server=server, job_id=job_id)
            click.echo(job_info)

        @click.command(name='list')
        @click.argument('job_ids', type=JobIDRangeParamType(), nargs=-1)
        def job_list(job_ids):
            """list info for multiple jobs
            """
            job_ids = [x for x in itertools.chain(*job_ids)]  # make into one list
            server = self.get_active_server()
            job_infos = self.client_tool.get_job_info_list(server=server, job_ids=list(job_ids))
            click.echo(job_infos.as_table_string())

        @click.command()
        @click.argument('job_id', type=str)
        def reset(job_id):
            """reset job, process again
            """
            server = self.get_active_server()
            job_info = self.client_tool.reset_job(server=server, job_id=job_id)
            click.echo(job_info)

        @click.command()
        @click.argument('job_id', type=str)
        def cancel(job_id):
            """set job status to inactive """
            server = self.get_active_server()
            job_info = self.client_tool.cancel_job(server=server, job_id=job_id)
            click.echo(job_info)

        for func in [info, reset, cancel, job_list]:
            job.add_command(func)
        return job

    def get_user_commands(self):
        """Click group and commands for the 'user' subcommand

        """

        @click.group()
        def user():
            """manage API credentials"""
            pass

        @click.command()
        def info():
            """show current credentials"""
            click.echo(
                f"username is {self.settings.user_name}\nAPI token: {self.settings.user_token}"
            )

        @click.command()
        @click.argument('user_name', type=str)
        def set_username(user_name):
            """Set the given username in settings
            """
            self.settings.user_name = user_name
            self.settings.save()
            click.echo(f"username is now '{user_name}'")

        @click.command()
        def get_token():
            token = "".join(
                random.SystemRandom().choice(
                    string.ascii_uppercase + string.ascii_lowercase + string.digits
                )
                for _ in range(64)
            )
            self.settings.user_token = token
            self.settings.save()
            click.echo(
                f"Got and saved api token for username {self.settings.user_name}"
            )

        for func in [info, set_username, get_token]:
            user.add_command(func)
        return user

    def get_batch_commands(self):
        """Click group and commands for the 'batch' subcommand

        """

        @click.group()
        def batch():
            """manage anonymization job batches"""
            pass

        @click.command()
        def init():
            """Save an empty batch in the current folder, for current server"""
            batch_folder = self.get_batch_folder()
            if batch_folder.has_batch():
                raise AnonCommandLineParserException(
                    "Cannot init, A batch is already defined in this folder"
                )
            else:
                server = self.get_active_server()
                batch_folder.save(JobBatch(job_ids=[], server=server))
                click.echo(f"Initialised batch for {server} in current dir")

        @click.command()
        def info():
            click.echo(self.get_batch().to_string())

        @click.command()
        def delete():
            """delete batch in current folder"""
            self.get_batch_folder().delete_batch()
            click.echo(f"Removed batch in current dir")

        @click.command()
        @click.argument('job_ids', type=JobIDRangeParamType(), nargs=-1)
        def add(job_ids):
            """Add ids to current batch. Will not add already existing. Space separated, ranges like 1-40
            allowed
            """
            job_ids = [x for x in itertools.chain(*job_ids)]  # make into one list
            batch_folder = self.get_batch_folder()
            batch: JobBatch = batch_folder.load()
            batch.job_ids = sorted(list(set(batch.job_ids) | set(job_ids)))
            batch_folder.save(batch)
            click.echo(f"Added {job_ids} to batch")

        @click.command()
        @click.argument('job_ids', type=JobIDRangeParamType(), nargs=-1)
        def remove(job_ids):
            """Remove ids from current batch. Space separated, ranges like 1-40 allowed
            """
            job_ids = [x for x in itertools.chain(*job_ids)]  # make into one list
            batch_folder = self.get_batch_folder()
            batch: JobBatch = batch_folder.load()
            batch.job_ids = sorted(list(set(batch.job_ids) - set(job_ids)))
            batch_folder.save(batch)

            click.echo(f"Removed {job_ids} from batch")

        @click.command()
        def status():
            """Print status overview for all jobs in batch"""
            batch = self.get_batch()
            ids_queried = batch.job_ids
            try:
                infos = self.client_tool.get_job_info_list(
                    server=batch.server, job_ids=ids_queried
                )
            except ClientToolException as e:
                click.echo(e)

            click.echo(f"Job info for {len(infos)} jobs on {batch.server}:")
            click.echo(infos.as_table_string())

            summary = ["Status       count   percentage", "-------------------------------"]
            status_count = Counter([x.status for x in infos])
            status_count["NOT_FOUND"] = len(ids_queried) - len(infos)
            for key, value in status_count.items():
                percentage = f"{(value / len(ids_queried) * 100):.1f} %"
                msg = f"{key:<12} {str(value):<8} {percentage:<8}"
                summary.append(msg)

            summary.append("-------------------------------")
            summary.append(f"Total        {str(len(ids_queried)):<8} 100%")

            click.echo(f"Summary for all {len(ids_queried)} jobs:")
            click.echo("\n".join(summary))

        @click.command()
        def reset():
            """Reset every job in the current batch"""
            batch: JobBatch = self.get_batch()

            if click.confirm(
                f"This will reset {len(batch.job_ids)} jobs on {batch.server}. Are you sure?"
            ):
                for job_id in batch.job_ids:
                    click.echo(
                        self.client_tool.reset_job(server=batch.server, job_id=job_id)
                    )

                click.echo("Done")
            else:
                click.echo("User cancelled")

        @click.command()
        def cancel():
            """Cancel every job in the current batch"""
            batch: JobBatch = self.get_batch()

            if click.confirm(
                f"This will cancel {len(batch.job_ids)} jobs on {batch.server}. Are you sure?"
            ):
                for job_id in batch.job_ids:
                    click.echo(
                        self.client_tool.cancel_job(server=batch.server, job_id=job_id)
                    )

                click.echo("Done")
            else:
                click.echo("User cancelled")

        @click.command()
        def reset_error():
            """Reset all jobs with error status in the current batch"""
            batch: JobBatch = self.get_batch()
            try:
                infos = self.client_tool.get_job_info_list(
                    server=batch.server, job_ids=batch.job_ids
                )
            except ClientToolException as e:
                click.echo(f"Error resetting: {str(e)}")
                return

            job_ids = [x.job_id for x in infos if x.status == JobStatus.ERROR]

            if click.confirm(
                f"This will reset {len(job_ids)} jobs on {batch.server}. Are you sure?"
            ):
                for job_id in job_ids:
                    click.echo(
                        self.client_tool.reset_job(server=batch.server, job_id=job_id)
                    )

                click.echo("Done")
            else:
                click.echo("User cancelled")

        for func in [info, status, reset, init, delete, add, remove, cancel, reset_error]:
            batch.add_command(func)
        return batch

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
            raise AnonCommandLineParserException("No batch defined in current folder")
        else:
            return batch

    def get_batch_folder(self):
        """True if there is a batch defined in this folder"""
        return BatchFolder(self.current_dir())


class AnonCommandLineParserException(Exception):
    pass


class ClientToolException(Exception):
    pass
