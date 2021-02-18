from anonapi.batch import BatchFolder, JobBatch
from anonapi.cli.batch_commands import add, cancel, info
from anonapi.client import ClientToolException
from anonapi.cli import entrypoint
from tests.mock_responses import RequestsMockResponseExamples


def test_command_without_defined_batch(mock_main_runner):
    """Try working with a batch of job ids from console"""

    runner = mock_main_runner

    assert "No batch defined" in str(
        runner.invoke(entrypoint.cli, "batch info", catch_exceptions=False).output
    )
    assert "No batch defined" in str(runner.invoke(info, catch_exceptions=False).output)
    assert "No batch defined" in str(runner.invoke(add, catch_exceptions=False).output)
    assert "No batch defined" in str(
        runner.invoke(cancel, catch_exceptions=False).output
    )


def test_cli_batch(mock_main_runner):
    """If a user types 'batch <anything>' without a batch being present, the
    exceptions should be similar and informative. Recreates #315
    """

    runner = mock_main_runner
    batch_dir = BatchFolder(mock_main_runner.get_context().current_dir)

    result = runner.invoke(entrypoint.cli, "batch info")
    assert "No batch defined" in str(result.output)

    assert not batch_dir.has_batch()
    runner.invoke(entrypoint.cli, "batch init")
    assert batch_dir.has_batch()

    # init again should fail as there is already a batch defined
    result = runner.invoke(entrypoint.cli, "batch init")
    assert "Cannot init" in str(result.output)

    runner.invoke(entrypoint.cli, "batch add 1 2 3 345")
    assert batch_dir.load().job_ids == ["1", "2", "3", "345"]

    runner.invoke(
        entrypoint.cli, "batch add 1 2 50"
    )  # duplicates should be silently ignored
    assert batch_dir.load().job_ids == ["1", "2", "3", "345", "50"]

    runner.invoke(
        entrypoint.cli, "batch remove 50 345 1000"
    )  # non-existing keys should be ignored
    assert batch_dir.load().job_ids == ["1", "2", "3"]

    runner.invoke(entrypoint.cli, "batch remove 1 2 3")
    assert batch_dir.load().job_ids == []

    runner.invoke(entrypoint.cli, "batch delete")
    assert not batch_dir.has_batch()


def test_cli_batch_status(mock_main_runner, mock_requests):
    """Try operations actually calling server"""
    runner = mock_main_runner
    # run batch status without a batch
    result = runner.invoke(entrypoint.cli, "batch status")
    assert result.exit_code == 1

    context = mock_main_runner.get_context()

    batch = JobBatch(
        job_ids=["1000", "1002", "5000"], server=context.get_active_server()
    )
    context.get_batch = lambda: batch  # set current batch to mock batch

    mock_requests.set_response_text(
        text=RequestsMockResponseExamples.JOBS_LIST_GET_JOBS_LIST
    )
    result = runner.invoke(entrypoint.cli, "batch status")
    assert all(
        text in result.output for text in ["DONE", "UPLOAD", "1000", "1002", "5000"]
    )


def test_cli_batch_status_extended(mock_main_runner, mock_requests):
    runner = mock_main_runner
    context = mock_main_runner.get_context()
    batch = JobBatch(
        job_ids=["1001", "1002", "1003"], server=context.get_active_server()
    )
    context.get_batch = lambda: batch  # set current batch to mock batch

    mock_requests.set_response_text(
        text=RequestsMockResponseExamples.JOBS_LIST_GET_JOBS_EXTENDED
    )
    result = runner.invoke(
        entrypoint.cli, "batch status --patient-name", catch_exceptions=False
    )
    assert all(
        text in result.output for text in ["1982", "DONE", "1001", "1002", "1003"]
    )

    # without the flag this should not be shown
    result = runner.invoke(entrypoint.cli, "batch status", catch_exceptions=False)
    assert "1982" not in result.output


def test_cli_batch_cancel(mock_main_runner_with_batch, mock_requests):
    """Try operations actually calling server"""
    runner = mock_main_runner_with_batch

    mock_requests.set_response_text(
        text=RequestsMockResponseExamples.JOBS_LIST_GET_JOBS_LIST
    )
    result = runner.invoke(entrypoint.cli, "batch cancel", input="No")
    assert "User cancelled" in result.output
    assert not mock_requests.requests.called

    mock_requests.reset()
    result = runner.invoke(entrypoint.cli, "batch cancel", input="Yes")
    assert "Cancelled job 1000" in result.output
    assert mock_requests.requests.post.call_count == 4


def test_cli_batch_status_errors(mock_main_runner_with_batch, mock_requests):
    """Call server, but not all jobs exist. This should appear in the status
    message to the user
    """
    runner = mock_main_runner_with_batch

    mock_requests.set_response_text(
        text=RequestsMockResponseExamples.JOBS_LIST_GET_JOBS_LIST
    )
    result = runner.invoke(entrypoint.cli, "batch status")
    assert "NOT_FOUND    1" in result.output


def test_cli_batch_reset(mock_main_runner_with_batch, mock_requests):

    runner = mock_main_runner_with_batch

    runner.invoke(entrypoint.cli, "batch reset", input="Yes")
    assert (
        mock_requests.requests.post.call_count == 4
    )  # Reset request should have been sent for each job id

    mock_requests.requests.reset_mock()
    runner.invoke(
        entrypoint.cli, "batch reset", input="No"
    )  # now answer no when asked are you sure
    assert (
        mock_requests.requests.post.call_count == 0
    )  # No requests should have been sent


def test_cli_batch_show_errors(mock_main_runner_with_batch, mock_requests):

    runner = mock_main_runner_with_batch
    mock_requests.set_response_text(
        text=RequestsMockResponseExamples.JOBS_LIST_GET_JOBS_LIST_WITH_ERROR
    )

    result = runner.invoke(entrypoint.cli, "batch show-error", catch_exceptions=False)
    assert result.exit_code == 0
    assert "Terrible error" in result.output


def test_cli_batch_reset_error(mock_main_runner_with_batch, mock_requests):
    """Try operations actually calling server"""
    runner = mock_main_runner_with_batch

    mock_requests.set_response_text(
        text=RequestsMockResponseExamples.JOBS_LIST_GET_JOBS_LIST_WITH_ERROR
    )

    # try a reset, answer 'Yes' to question
    result = runner.invoke(
        entrypoint.cli, "batch reset-error", input="Yes", catch_exceptions=False
    )
    assert result.exit_code == 0
    assert "This will reset 2 jobs on testserver" in result.output
    assert "Done" in result.output
    assert mock_requests.requests.post.called

    # now try the same but answer 'No'
    mock_requests.reset()
    result = runner.invoke(entrypoint.cli, "batch reset-error", input="No")
    assert result.exit_code == 0
    assert (
        not mock_requests.requests.post.called
    )  # cancelling should not have sent any requests

    # A reset where the server returns error
    mock_requests.reset()
    mock_requests.set_response_exception(ClientToolException("Terrible exception"))
    result = runner.invoke(entrypoint.cli, "batch reset-error", catch_exceptions=False)
    assert "Error:" in result.output


def test_cli_batch_id_range(mock_main_runner):
    """Check working with id ranges"""

    runner = mock_main_runner
    batch_dir = BatchFolder(mock_main_runner.get_context().current_dir)

    assert not batch_dir.has_batch()
    runner.invoke(entrypoint.cli, "batch init")
    assert batch_dir.has_batch()

    runner.invoke(entrypoint.cli, "batch add 1 2 5-8")
    assert batch_dir.load().job_ids == ["1", "2", "5", "6", "7", "8"]

    runner.invoke(entrypoint.cli, "batch remove 1-4")
    assert batch_dir.load().job_ids == ["5", "6", "7", "8"]

    runner.invoke(
        entrypoint.cli, "batch add 1-4 4"
    )  # check that duplicate values do not cause trouble
    assert batch_dir.load().job_ids == [
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
    ]
