"""Anonymization web API client. Can interface with Anonymization server to retrieve,
 create, modify anonymization jobs
"""

import requests
import json

from anonapi.objects import RemoteAnonServer
from anonapi.responses import (JobsInfoList, parse_job_infos_response,
                               APIParseResponseException, format_job_info_list,
                               JobInfo)


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

    def get(self, function_name, **kwargs):
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

        APIClientException:
            When server cannot be found

        """

        function_url = self.hostname + "/" + function_name

        # self.validate_https is false or true, but requests.get expects false or none to either validate or not
        if self.validate_https:
            validate = self.validate_https
        else:
            validate = None

        try:
            response = self.requestslib.get(
                function_url,
                data=self.add_user_name_to_args(kwargs),
                verify=validate,
                headers={"Authorization": f"Token {self.token}"},
            )
        except requests.exceptions.RequestException as e:
            raise APIClientException(e)

        self.interpret_response(response)
        return json.loads(response.text)

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

        APIClientException:
            When server cannot be found
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
            raise APIClientException(e)

        self.interpret_response(response)
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
        """ Query the API for info on all functions and parameters.

        Returns
        -------
        dict
            nested dict with info on all functions and parameters

        Raises
        ------
        APIClientException
            when documentation is not returned by server in the expected way

        """
        # call API without function to get hug to return standard 404 + documentation

        response = self.get("")

        return response["documentation"]

    def interpret_response(self, response):
        """Check HTTP response and throw helpful python exception if needed.

        Will raise errors for any response code other than 200(OK) and 404(Not found)

        Parameters
        ----------
        response: :obj:`requests.models.Response`
            A response such as it is returned by the python requests library

        Returns
        -------
            Nothing

        Raises
        ------
        APIClientAuthorizationFailedException:
            When username and or token is not accepted
        APIClientAPIException:
            When API call succeeds, but the API itself returns an error. For example 'missing parameter'.
        APIClientException:
            When any unexpected response is returned

        """

        if response.status_code == 200:
            # response succeeded, no further checking needed
            return

        elif response.status_code == 404:
            # 404 does not mean the API is unresponsive. This is returned for calling a function that does not
            # exist. The response is 404 and a helpful help message.

            # differentiate a 'good' API 404 from just any non API 404 response (bad). API 404 should be json parsable
            # and contain a key 'documentation'
            try:
                json_parsed = json.loads(response.text)
            except json.decoder.JSONDecodeError:
                msg = f"response from {self} was not JSON. Is this a web API url?"
                raise APIClientException(msg)
            if "documentation" not in json_parsed.keys():
                msg = f"No documentation found when calling {self} is this a web API?"
                raise APIClientException(msg)
            # if this all works its a valid API 404. No problem
            return

        elif response.status_code == 401:
            msg = "Server '{0}' returned 401 - Unauthorized, Your credentials do not seem to work".format(
                self.hostname
            )
            raise APIClientAuthorizationFailedException(msg)

        elif response.status_code == 400:
            error_response = json.loads(response.text)

            if "errors" in error_response.keys():
                errors = error_response["errors"]
            else:
                errors = error_response

            msg = f"API returns errors: {response.text}"
            raise APIClientAPIException(msg, api_errors=errors)

        elif response.status_code == 405:
            msg = (
                "'{0}' returned 405 - Method not allowed. Probably you are using GET where POST is "
                "needed, or vice versa. See APIClient.get_documentation() for usage"
            ).format(self)
            raise APIClientException(msg)

        else:
            msg = "Unexpected response from {0}: code '{1}', reason '{2}'".format(
                self, response.status_code, response.reason
            )
            raise APIClientException(msg)


class AnonClientTool:
    """Performs several actions via the Anonymization web API interface.

    One abstraction level above WebAPIClient. Client deals with https calls, get and
    post, this tool should not do any http operations, and instead deal with servers
    and jobs.
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

    def get_job_info_list(self, server: RemoteAnonServer, job_ids,
                          get_extended_info=False):
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
                [JobInfo(x) for x in client.get(api_function_name,
                                                job_ids=job_ids).values()]
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

    def create_path_job(
        self,
        server: RemoteAnonServer,
        anon_name,
        anon_id,
        project_name,
        source_path,
        destination_path,
        description,
    ):
        """Create a job with data coming from a network path

        Parameters
        ----------
        server: RemoteAnonServer
        anon_name: str
        anon_id: str
        project_name: str
        source_path: path
        destination_path: path
        description: str

        Raises
        ------
        APIClientException
            When anything goes wrong creating job

        Returns
        -------
        dict
            response from server with info on created job


        """

        client = self.get_client(server.url)

        info = client.post(
            "create_job",
            source_type="PATH",
            source_path=source_path,
            destination_type="PATH",
            project_name=project_name,
            destination_path=destination_path,
            anonymizedpatientname=anon_name,
            anonymizedpatientid=anon_id,
            description=description,
        )

        return info

    def create_pacs_job(
        self,
        server: RemoteAnonServer,
        anon_name,
        anon_id,
        source_instance_id,
        project_name,
        destination_path,
        description,
    ):
        """Create a job with data from a PACS system

        Parameters
        ----------
        server: RemoteAnonServer
        anon_name: str
        anon_id: str
        project_name: str
        source_instance_id: str
        destination_path: path
        description: str

        Raises
        ------
        APIClientException
            When anything goes wrong creating job

        Returns
        -------
        dict
            response from server with info on created job


        """
        client = self.get_client(server.url)

        info = client.post(
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
        )

        return info


class ClientInterfaceException(Exception):
    """A general problem with client interface """

    pass


class APIClientException(Exception):
    """A general problem with the APIClient """

    pass


class APIClient404Exception(Exception):
    """object not found. Made this into a separate function to be able to ignore it in special cases"""

    pass


class APIClientAuthorizationFailedException(APIClientException):
    pass


class APIClientAPIException(APIClientException):
    """The API was called successfully, but there was a problem within the API itself """

    def __init__(self, msg, api_errors):
        """

        Parameters
        ----------
        msg: text
            error message to show

        api_errors: dict(str)
            one key:value pair per error

        """

        super(APIClientAPIException, self).__init__(msg)
        self.api_errors = api_errors


class ClientToolException(Exception):
    pass
