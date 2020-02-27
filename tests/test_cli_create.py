from pathlib import Path, PureWindowsPath

import pytest

from anonapi.batch import BatchFolder
from anonapi.cli.create_commands import (
    main,
    JobParameterSet,
    ParameterMappingException,
    JobSetValidationError,
)
from anonapi.mapper import MappingFolder
from anonapi.parameters import (
    SourceIdentifierParameter,
    FolderIdentifier,
    Description,
    SourceIdentifier,
    Parameter,
    PatientID,
    PIMSKey,
    RootSourcePath,
    ParameterException,
    ParameterSet,
)
from anonapi.settings import JobDefaultParameters
from tests.mock_responses import RequestsMockResponseExamples


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
    assert result.exit_code == 1
    assert "No mapping" in result.output


def test_create_from_mapping(mock_from_mapping_runner, mock_requests_for_job_creation):
    """Try from-mapping, creating jobs based on a mapping"""

    # Run and answer are you sure 'N'
    result = mock_from_mapping_runner.invoke(
        main, "from-mapping", input="N", catch_exceptions=False
    )
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
    """Source identifiers in mappings are usually given as relative paths. However,
    jobs should be created with absolute, unambiguous paths. Check that this
    conversion works

    """
    result = mock_from_mapping_runner.invoke(
        main, "from-mapping", input="Y", catch_exceptions=False
    )
    assert result.exit_code == 0
    assert mock_requests_for_job_creation.requests.post.call_count == 20

    current_dir = str(mock_from_mapping_runner.mock_context.current_dir)
    mapping = MappingFolder(current_dir).load_mapping()

    def all_paths(mapping_in):
        """List[str] of all paths in mapping"""
        return [
            str(x)
            for y in mapping_in.rows()
            for x in y
            if isinstance(x, SourceIdentifierParameter)
        ]

    # in mapping there should be no mention of the current dir
    assert not any([current_dir in x for x in all_paths(mapping)])
    expected_root = (
        ParameterSet(mapping.options).get_param_by_type(RootSourcePath).value
    )
    # But in the created jobs the current dir should have been added
    assert str(expected_root) in str(
        mock_requests_for_job_creation.requests.post.call_args[1]["data"]["source_path"]
    )


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


def test_job_parameter_set(all_parameters):
    """Map Parameter objects to their parameter names in job-creation functions"""
    mapped = JobParameterSet(all_parameters).as_kwargs()
    assert mapped["anon_name"] == "patientName0"

    # sending an unknown parameter will raise an exception
    class UnknownIdentifier(SourceIdentifier):
        pass

    with pytest.raises(ParameterMappingException):
        JobParameterSet(
            all_parameters + [SourceIdentifierParameter(str(UnknownIdentifier(None)))]
        ).as_kwargs()

    class UnknownParameter(Parameter):
        pass

    with pytest.raises(ParameterMappingException):
        JobParameterSet(all_parameters + [UnknownParameter()]).as_kwargs()


def test_job_parameter_set_validate(all_parameters):
    """Test specific problems in job parameter sets"""
    param_set = JobParameterSet(all_parameters)

    # this should not raise anything
    param_set.validate()

    # now without a root source root_path, it is not possible to know what the
    # relative root_path parameters are referring to. Exception.
    param_set.parameters.remove(param_set.get_param_by_type(RootSourcePath))
    with pytest.raises(JobSetValidationError) as e:
        param_set.validate()


def test_job_parameter_set_validate_non_unc_paths(all_parameters):
    """Windows maps drive letters, makes then unaccessible to normal
     python code and then forbids using anything BUT drive letters in windows cmd
     A very annoying combination which makes it hard to determine what a path is
     in windows. Just make sure no jobs can be created with drive letters any paths
     """

    param_set = JobParameterSet(all_parameters)
    root_source = param_set.get_param_by_type(RootSourcePath)
    root_source.value = PureWindowsPath(r"Z:\folder1")
    with pytest.raises(JobSetValidationError) as e:
        param_set.validate()


def test_job_parameter_set_defaults():
    """You can set defaults for a parameter set. These are only kept if not
    overwritten """

    param_set = JobParameterSet(
        [PatientID("1234"), PIMSKey("0000")],
        default_parameters=[Description("Default")],
    )
    assert param_set.get_param_by_type(Description).value == "Default"

    param_set2 = JobParameterSet(
        [PatientID("1234"), Description("Overwrite!")],
        default_parameters=[Description("Default")],
    )
    assert param_set2.get_param_by_type(Description).value == "Overwrite!"
