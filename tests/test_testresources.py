from anonapi.testresources import (
    MockAnonClientTool,
    JobInfoFactory,
    RemoteAnonServerFactory,
    JobStatus,
)


def test_mock_anon_client_tool():
    some_responses = [
        JobInfoFactory(status=JobStatus.DONE),
        JobInfoFactory(status=JobStatus.ERROR),
        JobInfoFactory(status=JobStatus.INACTIVE),
    ]
    tool = MockAnonClientTool(responses=some_responses)
    server = RemoteAnonServerFactory()

    assert tool.get_job_info(server=server, job_id=1).status == JobStatus.DONE
    assert [x.status for x in tool.get_job_info_list(server, [1, 2, 3])] == [
        JobStatus.ERROR,
        JobStatus.INACTIVE,
        JobStatus.DONE,
    ]
