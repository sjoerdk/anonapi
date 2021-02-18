"""Anonymization web API client. Can interface with Anonymization server to retrieve,
create, modify anonymization jobs
"""
from typing import Dict

import requests
import json

from requests.exceptions import RequestException
from requests.models import Response

from anonapi.exceptions import AnonAPIException
from anonapi.objects import RemoteAnonServer
from anonapi.responses import (
    JobsInfoList,
    parse_job_infos_response,
    APIParseResponseException,
    format_job_info_list,
    JobInfo,
)


class WebAPIClient:
    def __init__(self, hostname, username, token, validate_https=True):
        """Makes calls to hug web API, handles errors

        Parameters
        ----------
        hostname: str
            url to web API that this client connects to
        username: str
            user name to use to log in to api
        token: str
            token to use to authenticate user with api
        validate_https: bool, optional
            if True, raise error if api https certificate cannot be verified. If
            False, just show warning. Default value True

        """

        self.hostname = hostname
        self.username = username
        self.token = token
        self.validate_https = bool(validate_https)
        self.requestslib = requests  # mostly for clean testing. Allows to switch
        # out the actual http-calling code

    def __str__(self):
        return f"WebAPIClient for {self.username}@{self.hostname}"

    def get(self, function_name, **kwargs) -> Dict:
        """Call this api, get response back

        Parameters
        ----------
        function_name: str
            API function to call
        kwargs:
            arguments for the API call


        Returns
        -------
        dict:
            dictionary with the results of the API call

        Raises
        ------
        APIClientAuthorizationFailedException:
            when authorization fails

        APIClientAPIException:
            when API call is successful, but the API returns some reason for error
            (for example 'job_id not found', or 'missing parameter')

        ServerNotResponding(APIClientException):
            When server is not responding at all

        APIClientException:
            When server is responding, but the response cannot be parsed
        """

        function_url = self.hostname + "/" + function_name

        try:
            response = self.requestslib.get(
                function_url,
                data=self.add_user_name_to_args(kwargs),
                verify=self.validate_https,
                headers={"Authorization": f"Token {self.token}"},
            )
        except RequestException as e:
            raise ServerNotResponding(e)

        return self.parse_response(response)

    def post(self, function_name, **kwargs):
        """Call this api, get response back

        Parameters
        ----------
        function_name: str
            API function to call
        kwargs:
            arguments for the API call


        Returns
        -------
        dict:
            dictionary with the results of the API call

        Raises
        ------
        APIClientAuthorizationFailedException:
            when authorization fails

        APIClientAPIException:
            when API call is successful, but the API returns some reason for error (for example 'job_id not found',
            or 'missing parameter')

        ServerNotResponding(APIClientException):
            When server is not responding at all

        APIClientException:
            When server is responding, but the response cannot be parsed
        """

        function_url = self.hostname + "/" + function_name
        try:
            response = self.requestslib.post(
                function_url,
                data=self.add_user_name_to_args(kwargs),
                verify=self.validate_https,
                headers={"Authorization": f"Token {self.token}"},
            )
        except requests.exceptions.RequestException as e:
            raise ServerNotResponding(e)

        self.parse_response(response)
        return json.loads(response.text)

    def add_user_name_to_args(self, args_in):
        """Add parameter 'user_name' to args_in using username found in settings, unless 'user_name' is is already
        defined

        Parameters
        ----------
        args_in: Dict(str, str)
            such as caught by a function in kwargs

        Returns
        -------
        Dict(str,str)
            args_in plus an additional dict tag_action 'user_name':<username from settings>

        """

        if "user_name" not in args_in.keys():
            args_in["user_name"] = self.username

        return args_in

    def get_documentation(self):
        """Query the API for info on all functions and rows.

        Returns
        -------
        dict
            nested dict with info on all functions and rows

        Raises
        ------
        APIClientException
            when documentation is not returned by server in the expected way

        """
        # call API without function to get hug to return standard 404 + documentation

        response = self.get("")

        return response["documentation"]

    def parse_json(self, text: str) -> Dict:
        """Parse string as json

        Raises
        ------
        APIClientException
            If parsing fails

        Returns
        -------
        Dict
            Json parsed
        """
        try:
            return json.loads(text)
        except json.decoder.JSONDecodeError:
            msg = f"response from {self} was not JSON. Is this a web API url?"
            raise APIClientException(msg)

    def parse_response(self, response: Response) -> Dict:
        """Extract a anonAPI dictionary from raw HTTP response

        Parameters
        ----------
        response: Response
            A response such as it is returned by the python requests library

        Raises
        ------
        APIClientAuthorizationFailedException:
            When username and or token is not accepted
        APIClientAPIException:
            When API call succeeds, but the API itself returns an error. For example
            'missing parameter'.
        APIClientException:
            When any unexpected response is returned

        """

        if response.status_code == 200:
            return self.parse_json(response.text)

        elif response.status_code == 404:
            # 404 does not mean the API is unresponsive. This is returned for
            # calling a function that does not exist for example.

            # differentiate a 'good' API 404 from just any non API 404 response
            # (bad). API 404 should be json parsable and contain a key 'documentation'
            json_parsed = self.parse_json(response.text)
            if "documentation" in json_parsed.keys():
                return json_parsed
            else:
                raise APIClientException(
                    f"No documentation found when calling {self} is this a web API?"
                )

        elif response.status_code == 401:
            raise APIClientAuthorizationFailedException(
                f"Server '{self.hostname}' returned 401 - Unauthorized, Your"
                f" credentials do not seem to work"
            )

        elif response.status_code == 400:
            # API responds correctly, but indicates an error. Pass this error on
            raise APIClientAPIException(
                f"API returns errors: {response.text}",
                api_errors=self.parse_json(response.text).get("errors", None),
            )

        elif response.status_code == 405:
            raise APIClientException(
                f"'{self}' returned 405 - Method not allowed. Probably you are "
                f"using GET where POST is needed, or vice versa. See "
                f"APIClient.get_documentation() for usage"
            )

        else:
            raise APIClientException(
                f"Unexpected response from {self}: code '{response.status_code}'"
                f", reason '{response.reason}'"
            )


class AnonClientTool:
    """Performs several actions via the Anonymization web API interface.

    One abstraction level above WebAPIClient. Client deals with https calls, get and
    post, this tool should not do any http operations, and instead deal with servers
    and jobs.

    Information about jobs is done trough JobInfo instances where possible
    """

    def __init__(self, username, token, validate_https=True):
        """Create an anonymization web API client tool

        Parameters
        ----------
        username: str
            use this when calling API
        token:
            API token to use when calling API
        validate_https: bool, optional
            If false, ignore all ssl errors

        """
        self.username = username
        self.token = token
        self.validate_https = validate_https

    def get_client(self, url):
        """Create an API client with the information in this tool

        Returns
        -------
        WebAPIClient
        """
        client = WebAPIClient(
            hostname=url,
            username=self.username,
            token=self.token,
            validate_https=self.validate_https,
        )
        return client

    def get_server_status(self, server: RemoteAnonServer) -> str:
        """

        Returns
        -------
        str:
            status of the given server
        """
        client = self.get_client(server.url)
        try:
            client.get_documentation()  # just test connectivity here
            return f"OK: {server} is online and responsive"
        except ServerNotResponding as e:
            return (
                f"Server '{server}' cannot be reached. Is the URL correct?. "
                f"Original Error:\n {str(e)}"
            )
        except APIClientException as e:
            return f"ERROR: '{server}' is not responding properly. Error:\n {str(e)}"

    def get_job_info(self, server: RemoteAnonServer, job_id: int) -> JobInfo:
        """Full description of a single job

        Parameters
        ----------
        server: :obj:`RemoteAnonServer`
            get job info from this server
        job_id: str
            id of job to get info for

        Raises
        ------
        ClientToolException:
            if something goes wrong getting jobs info from server

        Returns
        -------
        JobInfo:
            Information for the job

        """

        client = self.get_client(server.url)
        response_dict = client.get("get_job", job_id=job_id)

        return JobInfo.from_json(response_dict)

    def get_job_info_list(
        self, server: RemoteAnonServer, job_ids, get_extended_info=False
    ) -> JobsInfoList:
        """Get a list of info on the given job ids.

        Parameters
        ----------
        server: RemoteAnonServer
            get job info from this server
        job_ids: List[str]
            list of jobs to get info for
        get_extended_info: Boolean, optional
            query API for additional info about source and destination. Made this
            optional because the resulting DB query is bigger. Might be slower.
            Defaults to False, meaning only core info is retrieved

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
        if get_extended_info:
            api_function_name = "get_jobs_list_extended"
        else:
            api_function_name = "get_jobs_list"
        try:
            return JobsInfoList(
                [
                    JobInfo.from_json(x)
                    for x in client.get(api_function_name, job_ids=job_ids).values()
                ]
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
            input describing job, or error if job could not be found

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
            a input describing success or any API error
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
            a input describing success or any API error
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

    def set_opt_out_ignore(self, server: RemoteAnonServer, job_id: str, reason: str):
        """Set opt-out ignore with a reason for given job

        Returns
        -------
        str
            a input describing success or any API error
        """

        client = self.get_client(server.url)
        try:
            _ = client.post(
                "modify_job",
                job_id=job_id,
                source_ignore_opt_out=True,
                source_ignore_opt_out_reason=f"Reason: {reason}",
            )
            info = f"Set opt-out ignore ({reason}) for job {job_id} on {server}"
        except APIClientException as e:
            info = f"Error setting opt-out ignore on{server.name}:\n{str(e)}"
        return info

    def create_path_job(
        self,
        server: RemoteAnonServer,
        project_name,
        source_path,
        destination_path,
        description,
        anon_name=None,
        anon_id=None,
        pims_keyfile_id=None,
    ) -> JobInfo:
        """Create a job with data coming from a network root_path

        Parameters
        ----------
        server: RemoteAnonServer
        project_name: str
        source_path: root_path
        destination_path: root_path
        description: str
        anon_name: str, optional
            Patient name to set in anonymized data. Can be omitted if pims_keyfile_id
            is given
        anon_id: str, optional
            Patient id to set in anonymized data. Can be omitted if pims_keyfile_id
            is given
        pims_keyfile_id: str, optional
           pims keyfile to use. Defaults to no pims keyfile

        Raises
        ------
        APIClientException
            When anything goes wrong creating job

        Returns
        -------
        JobInfo
            response from server with info on created job


        """

        client = self.get_client(server.url)

        response_dict = client.post(
            "create_job",
            source_type="PATH",
            source_path=source_path,
            destination_type="PATH",
            project_name=project_name,
            destination_path=destination_path,
            anonymizedpatientname=anon_name,
            anonymizedpatientid=anon_id,
            description=description,
            pims_keyfile_id=pims_keyfile_id,
        )

        return JobInfo.from_json(response_dict)

    def create_pacs_job(
        self,
        server: RemoteAnonServer,
        source_instance_id,
        project_name,
        destination_path,
        description,
        anon_name=None,
        anon_id=None,
        pims_keyfile_id=None,
    ) -> JobInfo:
        """Create a job with data from a PACS system

        Parameters
        ----------
        server: RemoteAnonServer
        project_name: str
        source_instance_id: str
        destination_path: root_path
        description: str
        anon_name: str, optional
            Patient name to set in anonymized data. Can be omitted if pims_keyfile_id
            is given
        anon_id: str, optional
            Patient id to set in anonymized data. Can be omitted if pims_keyfile_id
            is given
        pims_keyfile_id: str, optional
           pims keyfile to use. Defaults to no pims keyfile

        Raises
        ------
        APIClientException
            When anything goes wrong creating job

        Returns
        -------
        JobInfo
            response from server with info on created job


        """
        client = self.get_client(server.url)

        response_dict = client.post(
            "create_job",
            source_type="WADO",
            source_name="IDC_WADO",
            source_instance_id=source_instance_id,
            destination_type="PATH",
            project_name=project_name,
            destination_path=destination_path,
            anonymizedpatientname=anon_name,
            anonymizedpatientid=anon_id,
            description=description,
            pims_keyfile_id=pims_keyfile_id,
        )

        return JobInfo.from_json(response_dict)


class ClientInterfaceException(AnonAPIException):
    """A general problem with client interface"""

    pass


class APIClientException(AnonAPIException):
    """A general problem with the APIClient"""

    pass


class ServerNotResponding(APIClientException):
    """API server is not responding at all"""

    pass


class APIClient404Exception(AnonAPIException):
    """Object not found. Made this into a separate function to be able to ignore
    it in special cases
    """

    pass


class APIClientAuthorizationFailedException(APIClientException):
    pass


class APIClientAPIException(APIClientException):
    """The API was called successfully, but there was a problem within the API
    itself
    """

    def __init__(self, msg, api_errors):
        """

        Parameters
        ----------
        msg: text
            error message to show

        api_errors: dict(str)
            one key:value pair per error

        """

        super().__init__(msg)
        self.api_errors = api_errors


class ClientToolException(AnonAPIException):
    pass
