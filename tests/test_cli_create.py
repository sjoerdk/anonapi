from pathlib import Path

import pytest

from anonapi.batch import BatchFolder
from anonapi.cli.create_commands import main
from anonapi.mapper import MappingListFolder
from anonapi.settings import JobDefaultParameters
from tests.factories import RequestsMockResponseExamples


@pytest.fixture()
def mock_main_runner_with_mapping(mock_main_runner, a_folder_with_mapping):
    """Mock runner where a mapping is defined in current dir"""
    mock_main_runner.set_mock_current_dir(a_folder_with_mapping)
    return mock_main_runner


@pytest.fixture()
def mock_from_mapping_runner(mock_main_runner_with_mapping):
    """Mock runner that has everything to make a call to from-mapping work:
    * Mapping defined in current dir
    * Default job parameters are non-empty"""

    parameters = (
        mock_main_runner_with_mapping.get_context().settings.job_default_parameters
    )
    parameters.project_name = "test_project"
    parameters.destination_path = Path("//test/output/path")

    return mock_main_runner_with_mapping


@pytest.fixture()
def mock_requests_for_job_creation(mock_requests):
    """Mock requests library so that every call to it will return a standard
    anonapi Job created response
    """
    mock_requests.set_response(RequestsMockResponseExamples.JOB_CREATED_RESPONSE)
    return mock_requests


def test_create_from_mapping_no_mapping(mock_main_runner):
    """Running from-mapping in a folder without mapping should not work"""
    result = mock_main_runner.invoke(main, "from-mapping")
    assert result.exit_code == 0
    assert "No mapping" in result.output


def test_create_from_mapping(mock_from_mapping_runner,
                             mock_requests_for_job_creation):
    """Try from-mapping, creating jobs based on a mapping"""

    # Run and answer are you sure 'N'
    result = mock_from_mapping_runner.invoke(main, "from-mapping", input="N",
                                             catch_exceptions=False)
    assert result.exit_code == 0
    assert "Cancelled" in result.output
    assert mock_requests_for_job_creation.requests.post.call_count == 0

    # Now answer Y
    result = mock_from_mapping_runner.invoke(
        main, "from-mapping", input="Y", catch_exceptions=False
    )
    assert result.exit_code == 0
    assert mock_requests_for_job_creation.requests.post.call_count == 20
    batch_folder = BatchFolder(mock_from_mapping_runner.mock_context.current_dir)
    assert batch_folder.has_batch()
    assert batch_folder.load().job_ids == [
        1234
    ]  # only 1 id as mock requests returns the same job id each call


def test_create_from_mapping_server_error(mock_from_mapping_runner, mock_requests):
    """Try from-mapping, when job creation will yield an error from server"""

    mock_requests.set_responses(
        [RequestsMockResponseExamples.ERROR_USER_NOT_CONNECTED_TO_PROJECT]
    )
    result = mock_from_mapping_runner.invoke(
        main, "from-mapping", input="Y", catch_exceptions=False
    )
    assert result.exit_code == 0
    assert mock_requests.requests.post.call_count == 1
    batch_folder = BatchFolder(mock_from_mapping_runner.mock_context.current_dir)
    assert (
        not batch_folder.has_batch()
    )  # No batch should be there as all creation failed!


def test_create_from_mapping_server_error_halfway(
    mock_from_mapping_runner, mock_requests
):
    """What if an error occurs halfway through? """

    mock_requests.set_responses(
        [
            RequestsMockResponseExamples.JOB_CREATED_RESPONSE,
            RequestsMockResponseExamples.JOB_CREATED_RESPONSE,
            RequestsMockResponseExamples.ERROR_USER_NOT_CONNECTED_TO_PROJECT,
        ]
    )
    result = mock_from_mapping_runner.invoke(
        main, "from-mapping", input="Y", catch_exceptions=False
    )
    assert result.exit_code == 0
    assert mock_requests.requests.post.call_count == 3
    batch_folder = BatchFolder(mock_from_mapping_runner.mock_context.current_dir)
    assert batch_folder.has_batch()
    assert batch_folder.load().job_ids == [1234]


def test_create_set_default_parameters(
    mock_main_runner_with_mapping, mock_requests_for_job_creation
):
    # Try to run from-mapping
    result = mock_main_runner_with_mapping.invoke(main, "from-mapping", input="Y")

    # This should not work because essential settings are missing
    assert result.exit_code == 1
    assert "Could not find default project name" in result.output
    assert mock_requests_for_job_creation.requests.post.call_count == 0

    # set them
    result = mock_main_runner_with_mapping.invoke(
        main, "set-defaults", input="some_project\n//network/test/path\n"
    )
    assert result.exit_code == 0

    # Now this command should succeed
    result = mock_main_runner_with_mapping.invoke(main, "from-mapping", input="Y")
    assert result.exit_code == 0
    assert mock_requests_for_job_creation.requests.post.call_count == 20


def test_show_set_default_parameters(mock_main_runner):
    # Try to run from-mapping
    parameters: JobDefaultParameters = mock_main_runner.get_context().settings.job_default_parameters
    parameters.project_name = "test_project"
    parameters.destination_path = "test_destination"

    result = mock_main_runner.invoke(main, "show-defaults")
    assert result.exit_code == 0
    assert all(x in result.output for x in ["test_project", "test_destination"])


def test_create_from_mapping_relative_path(
    mock_from_mapping_runner, mock_requests_for_job_creation
):
    """Source identifiers in mappings are usually given as relative paths. However, jobs should be created with
    absolute, unambiguous paths. Check that this conversion works

    """
    result = mock_from_mapping_runner.invoke(
        main, "from-mapping", input="Y", catch_exceptions=False
    )
    assert result.exit_code == 0
    assert mock_requests_for_job_creation.requests.post.call_count == 20

    current_dir = str(mock_from_mapping_runner.mock_context.current_dir)
    batch_folder = BatchFolder(current_dir)
    mapping_folder = MappingListFolder(current_dir)
    paths_in_mapping = map(str, list(mapping_folder.load_list().keys()))
    # in mapping there should be no mention of the current dir
    assert not any([current_dir in x for x in paths_in_mapping])
    # But in the created jobs the current dir should have been added
    assert current_dir in str(mock_requests_for_job_creation.requests.post.call_args)


def test_create_from_mapping_dry_run(
    mock_from_mapping_runner, mock_requests_for_job_creation
):
    """Test dry run mode. Should not hit anything important
    """

    result = mock_from_mapping_runner.invoke(
        main, "from-mapping --dry-run", input="Y", catch_exceptions=False
    )
    assert result.exit_code == 0
    assert "Dry run" in result.output
    assert "patient4" in result.output
    assert mock_requests_for_job_creation.requests.post.call_count == 0


def test_create_from_mapping_folder_and_pacs(
    mock_from_mapping_runner,
    a_folder_with_mapping_diverse,
    mock_requests_for_job_creation,
):
    """PACS identifiers should generate slightly different jobs then Folder identifiers."""
    mock_requests = mock_requests_for_job_creation
    mock_from_mapping_runner.set_mock_current_dir(a_folder_with_mapping_diverse)

    result = mock_from_mapping_runner.invoke(
        main, "from-mapping", input="Y", catch_exceptions=False
    )
    assert result.exit_code == 0
    assert "Error:" not in result.output
    assert mock_requests.requests.post.call_count == 4

    batch_folder = BatchFolder(mock_from_mapping_runner.mock_context.current_dir)
    assert batch_folder.has_batch()
    assert batch_folder.load().job_ids == [
        1234
    ]  # only 1 id as mock requests returns the same job id each call
