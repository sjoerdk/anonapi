"""Resources for testing external code that imports anonapi

Generates realistic api call return values without actually calling or needing
an IDIS server

Example:

from anonapi.responses import JobStatus
from anonapi.testresources import MockAnonClientTool, JobInfoFactory, \
    RemoteAnonServerFactory

tool = MockAnonClientTool(
    responses=[JobInfoFactory(status=JobStatus.DONE),
               JobInfoFactory(status=JobStatus.ERROR),
               JobInfoFactory(status=JobStatus.INACTIVE)])

info = tool.get_job_info(server=RemoteAnonServerFactory(), job_id=100)
info.status  # DONE
info.job_id  # 100  (matches whatever you put in it)

"""
from itertools import cycle
from typing import List

import factory

from anonapi.client import AnonClientTool
from anonapi.objects import RemoteAnonServer
from anonapi.responses import JobInfo, JobsInfoList, JobStatus

class MockAnonClientTool(AnonClientTool):
    """A client tool that does not hit any server. Returns mocked responses

    job_id in mocked return values will be altered to any job_id requested
    """

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

        self.response_generator = self.get_response_generator(responses)

    def set_responses(self, responses: List[JobInfo]):
        """Return these responses for any method call. Cycle if depleted"""
        self.response_generator = self.get_response_generator(responses)

    @staticmethod
    def get_response_generator(responses: List[JobInfo]):
        return cycle(responses)

    def get_response(self, job_id: int) -> JobInfo:
        job_info = next(self.response_generator)
        job_info.job_id = job_id
        return job_info

    def get_client(self, _):
        # Just to be sure. Client should never be invoked
        raise NotImplemented("Mock client has no API client")

    def get_job_info(self, server: RemoteAnonServer, job_id: int) -> JobInfo:
        return self.get_response(job_id)

    def get_job_info_list(
        self, server: RemoteAnonServer, job_ids, get_extended_info=False
    ) -> JobsInfoList:
        return JobsInfoList([self.get_response(x) for x in job_ids])

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

        return next(self.response_generator)

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

        return next(self.response_generator)


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
