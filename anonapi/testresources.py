""" Generates realistic api call return values without actually calling or needing
a server

Putting this module here in main package because methods and classes are useful
for libs importing anonapi.

Tests for anonapi itself are still kept in /tests
"""
from itertools import cycle
from typing import List

import factory

from anonapi.client import AnonClientTool
from anonapi.objects import RemoteAnonServer
from anonapi.responses import JobInfo, JobsInfoList


class MockAnonClientTool(AnonClientTool):
    """A client tool that does not hit any server. Returns mocked responses"""

    def __init__(self, responses: List[JobInfo] = None):
        """

        Parameters
        ----------
        responses: List[JobInfo], optional
            Cycle through these when returning mock responses. Defaults to
            returning a single default JobInfo item over and over
        """
        super(MockAnonClientTool, self).__init__(
            username="mock_username", token="mock_token"
        )
        if not responses:
            responses = [JobInfoFactory()]

        self.response_generator = cycle(responses)

    def get_client(self, _):
        # Just to be sure. Client should never be invoked
        raise NotImplemented("Mock client has no API client")

    def get_job_info(self, server: RemoteAnonServer, job_id: int) -> JobInfo:
        return next(self.response_generator)

    def get_job_info_list(
        self, server: RemoteAnonServer, job_ids, get_extended_info=False
    ) -> JobsInfoList:
        return JobsInfoList(job_infos=[next(self.response_generator) for _ in job_ids])


class JobStatus:
    """All the states a job can be in"""

    INACTIVE = "INACTIVE"
    ACTIVE = "ACTIVE"
    ERROR = "ERROR"
    UPLOADED = "UPLOADED"
    DONE = "DONE"

    ALL = [INACTIVE, ACTIVE, ERROR, UPLOADED, DONE]


class JobInfoFactory(factory.Factory):
    """The object that is returned by get_job_info and get_job_infos """

    class Meta:
        model = JobInfo

    job_id = factory.sequence(lambda n: str(n))
    date = "2018-08-31T11:11:05"
    user_name = factory.sequence(lambda n: f"Z{n:07}")
    status = factory.Iterator(JobStatus.ALL)
    error = None
    description = factory.sequence(lambda n: f"Mock job {n}")
    project_name = "Wetenschap-Algemeen"
    priority = 10
    files_downloaded = None
    files_processed = None
    destination_id = factory.sequence(lambda n: f"{n+1}")
    destination_name = None
    destination_path = "\\\\resfilsp10\\imaging\\temp\\test_output"
    destination_network = None
    destination_status = "BASE"
    destination_type = "PATH"
    source_instance_id = None
    source_type = "PATH"
    source_anonymizedpatientid = None
    source_anonymizedpatientname = None
    source_name = None
    source_path = "f"
    source_protocol = "3178"


class RemoteAnonServerFactory(factory.Factory):
    """The object that is returned by get_job_info and get_job_infos """

    class Meta:
        model = RemoteAnonServer

    name = factory.sequence(lambda n: f"api server {n}")
    url = factory.sequence(lambda n: f"https://localhost/mockapiserver{n}")
