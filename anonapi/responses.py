""" Models things that an API server can send back. Bridge between raw json and
actual python objects

It would be much nicer to use an existing library that does serialization of
python models on the server side and the client side. But we're not using django yet.

"""

from collections import UserList
from typing import Dict

from tabulate import tabulate

from anonapi.exceptions import AnonAPIException


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

    Notes
    -----
    This whole implementation is shoddy. Moving to openAPI definition asap
    """

    def __init__(
        self,
        *,
        job_id,
        date,
        user_name,
        status,
        error="",
        description,
        project_name,
        priority=1,
        files_downloaded=0,
        files_processed=0,
        destination_id=0,
        destination_name=None,
        destination_path=None,
        destination_network=None,
        destination_status=None,
        destination_type=None,
        source_type=None,
        source_name=None,
        source_protocol=None,
        source_anonymizedpatientid=None,
        source_anonymizedpatientname=None,
        source_path=None,
        source_pims_keyfile_id=None,
        source_instance_id=None,
    ):
        self.job_id = job_id
        self.date = date
        self.user_name = user_name
        self.status = status
        self.error = error
        self.description = description
        self.project_name = project_name
        self.priority = priority
        self.files_downloaded = files_downloaded
        self.files_processed = files_processed

        self.destination_id = destination_id
        self.destination_name = destination_name
        self.destination_path = destination_path
        self.destination_network = destination_network
        self.destination_status = destination_status
        self.destination_type = destination_type

        self.source_type = source_type
        self.source_name = source_name
        self.source_protocol = source_protocol
        self.source_anonymizedpatientid = source_anonymizedpatientid
        self.source_anonymizedpatientname = source_anonymizedpatientname
        self.source_path = source_path
        self.source_pims_keyfile_id = source_pims_keyfile_id
        self.source_instance_id = source_instance_id

    @classmethod
    def from_json(cls, json_dict: Dict):
        """

        Parameters
        ----------
        json_dict: Dict
            API response as received from server

        """
        return cls(
            job_id=json_dict["job_id"],
            date=json_dict["date"],
            user_name=json_dict["user_name"],
            status=json_dict["status"],
            error=json_dict["error"],
            description=json_dict["description"],
            project_name=json_dict["project_name"],
            priority=json_dict["priority"],
            files_downloaded=json_dict["files_downloaded"],
            files_processed=json_dict["files_processed"],
            destination_path=json_dict.get("destination_path"),
            source_type=json_dict.get("source_type"),
            source_anonymizedpatientid=json_dict.get("source_anonymizedpatientid"),
            source_anonymizedpatientname=json_dict.get("source_anonymizedpatientname"),
            source_name=json_dict.get("source_name"),
            source_path=json_dict.get("source_path"),
            source_pims_keyfile_id=json_dict.get("source_pims_keyfile_id"),
            source_instance_id=json_dict.get("source_instance_id"),
        )

    def as_string(self):
        """As human readable  multi-line string"""
        to_print = {
            "job_id": self.job_id,
            "date": self.date,
            "user_name": self.user_name,
            "status": self.status,
            "error": self.error,
            "description": self.description,
            "project_name": self.project_name,
            "priority": self.priority,
            "files_downloaded": self.files_downloaded,
            "files_processed": self.files_processed,
            "destination_path": self.destination_path,
            "source_type": self.source_type,
            "source_anonymizedpatientid": self.source_anonymizedpatientid,
            "source_anonymizedpatientname": self.source_anonymizedpatientname,
            "source_name": self.source_name,
            "source_path": self.source_path,
            "source_pims_keyfile_id": self.source_pims_keyfile_id,
            "source_instance_id": self.source_instance_id,
        }

        return "\n".join([str(x) for x in to_print.items()])


class TableColumn:
    """A single column in a command_table"""

    def __init__(self, header, parameter_name):
        self.header = header
        self.parameter_name = parameter_name


class JobInfoColumns:
    """Columns that can be used in a command_table of JobInfos"""

    job_id = TableColumn(header="id", parameter_name="job_id")
    date = TableColumn(header="date", parameter_name="date")
    status = TableColumn(header="status", parameter_name="status")
    files_downloaded = TableColumn(header="down", parameter_name="files_downloaded")
    files_processed = TableColumn(header="proc", parameter_name="files_processed")
    user = TableColumn(header="user", parameter_name="user_name")
    pseudo_name = TableColumn(
        header="anon_name", parameter_name="source_anonymizedpatientid"
    )

    DEFAULT_COLUMNS = [job_id, date, status, files_downloaded, files_processed, user]
    EXTENDED_COLUMNS = DEFAULT_COLUMNS + [pseudo_name]


def format_job_info_list(job_infos, columns=JobInfoColumns.DEFAULT_COLUMNS):
    """To list that can be printed to console

    Parameters
    ----------
    job_infos: List[JobInfo]
        List of short infos
    columns: List[TableColumns], optional
        Show only these columns in command_table. Defaults to default columns for
        JobInfo objects

    Returns
    -------
    str:
        Nice string representation of this list

    """
    table = {
        column.header: [getattr(x, column.parameter_name) for x in job_infos]
        for column in columns
    }

    return tabulate(table, headers="keys", tablefmt="simple")


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
        return [JobInfo.from_json(x) for x in response.values()]
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
        """As a string with newlines, forming a neat command_table

        Parameters
        ----------
        columns: List[TableColumns], optional
            Show only these columns in command_table. Defaults to default columns for
            JobInfo objects

        Returns
        -------
        str:
            string with newlines

        """
        return format_job_info_list(self.data, columns=columns)


class APIParseResponseException(AnonAPIException):
    pass
