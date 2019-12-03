""" Models things that an API server can send back. Bridge between raw json and
actual python objects

It would be much nicer to use an existing library that does serialization of
python models on the server side and the client side. But we're not using django yet.

"""

from collections import UserList

from tabulate import tabulate


class JobStatus:
    """ Job status string the API server uses
    """

    ERROR = "ERROR"
    DONE = "DONE"
    UPLOADED = "UPLOADED"
    INACTIVE = "INACTIVE"
    ACTIVE = "ACTIVE"


class APIResponse:
    """A response from the Anonymizationserver web API
    """

    pass


class JobInfo:
    """Info on a single job. Makes it clear which fields should definitely be
    in the info, and which are optional
    """

    def __init__(self, json_raw):
        self.job_id = json_raw["job_id"]
        self.date = json_raw["date"]
        self.user_name = json_raw["user_name"]
        self.status = json_raw["status"]
        self.error = json_raw["error"]
        self.description = json_raw["description"]
        self.project_name = json_raw["project_name"]
        self.priority = json_raw["priority"]
        self.files_downloaded = json_raw["files_downloaded"]
        self.files_processed = json_raw["files_processed"]

        # extended parameters that might not be given
        self.destination_path = json_raw.get('destination_path')
        self.source_anonymizedpatientid = json_raw.get('source_anonymizedpatientid')
        self.source_anonymizedpatientname = json_raw.get(
            'source_anonymizedpatientname')
        self.source_path = json_raw.get('source_path')
        self.source_pims_keyfile_id = json_raw.get('source_pims_keyfile_id')
        self.source_instance_id = json_raw.get('source_instance_id')

        self.json_raw = json_raw


class TableColumn:
    """A single column in a table"""
    def __init__(self, header, parameter_name):
        self.header = header
        self.parameter_name = parameter_name


class JobInfoColumns:
    """Columns that can be used in a table of JobInfos"""
    job_id = TableColumn(header='id', parameter_name='job_id')
    date = TableColumn(header='date', parameter_name='date')
    status = TableColumn(header='status', parameter_name='status')
    files_downloaded = TableColumn(header='down',
                                   parameter_name='files_downloaded')
    files_processed = TableColumn(header='proc',
                                   parameter_name='files_processed')
    user = TableColumn(header='user', parameter_name='user_name')
    pseudo_name = TableColumn(header='anon_name',
                              parameter_name='source_anonymizedpatientid')

    DEFAULT_COLUMNS = [job_id, date, status, files_downloaded, files_processed, user]
    EXTENDED_COLUMNS = DEFAULT_COLUMNS + [pseudo_name]


def format_job_info_list(job_infos, columns=JobInfoColumns.DEFAULT_COLUMNS):
    """To list that can be printed to console

    Parameters
    ----------
    job_infos: List[JobInfo]
        List of short infos
    columns: List[TableColumns], optional
        Show only these columns in table. Defaults to default columns for
        JobInfo objects

    Returns
    -------
    str:
        Nice string representation of this list

    """
    table = {column.header: [x.json_raw.get(column.parameter_name) for x in job_infos]
             for column in columns}

    return tabulate(table, headers='keys', tablefmt='simple')


def parse_job_infos_response(response):
    """

    Parameters
    ----------
    response: dict
        API Response to 'get_jobs' method

    Raises
    ------
    APIParseResponseException:
        When response cannot be parsed

    Returns
    -------
    List(job_infos)

    """
    try:
        return [JobInfo(x) for x in response.values()]
    except (KeyError, AttributeError) as e:
        raise APIParseResponseException(
            f"Error parsing server response as job info: {e}"
        )


class JobsInfoList(UserList):
    def __init__(self, job_infos):
        """A list job infos that can be conveniently printed

        Parameters
        ----------
        job_infos: List(JobInfo)

        """
        self.data = job_infos

    def as_table_string(self, columns=JobInfoColumns.DEFAULT_COLUMNS):
        """As a string with newlines, forming a neat table

        Parameters
        ----------
        columns: List[TableColumns], optional
            Show only these columns in table. Defaults to default columns for
            JobInfo objects

        Returns
        -------
        str:
            string with newlines

        """
        return format_job_info_list(self.data, columns=columns)


class APIParseResponseException(Exception):
    pass
