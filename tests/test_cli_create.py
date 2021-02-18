from pathlib import PureWindowsPath
from typing import List, Tuple

import pytest

from anonapi.batch import BatchFolder
from anonapi.cli.create_commands import (
    CreateCommandsContext,
    from_mapping,
    main,
    JobParameterSet,
    ParameterMappingException,
    JobSetValidationError,
)
from anonapi.mapper import JobParameterGrid, Mapping
from anonapi.parameters import (
    DestinationPath,
    Project,
    PseudoName,
    SourceIdentifierParameter,
    Description,
    SourceIdentifier,
    Parameter,
    PseudoID,
    PIMSKey,
    RootSourcePath,
    ParameterSet,
)
from tests import RESOURCE_PATH
from tests.conftest import AnonAPIContextRunner
from tests.factories import FolderIdentifierFactory, StudyInstanceUIDIdentifierFactory
from tests.mock_responses import RequestsMockResponseExamples


@pytest.fixture()
def mock_requests_for_job_creation(mock_requests):
    """Mock requests library so that every call to it will return a standard
    anonapi Job created response
    """
    mock_requests.set_response(RequestsMockResponseExamples.JOB_CREATED_RESPONSE)
    return mock_requests


@pytest.fixture()
def a_create_command_context(mock_api_context) -> CreateCommandsContext:
    return CreateCommandsContext(mock_api_context)


def test_create_from_mapping_no_mapping(mock_main_runner):
    """Running from-mapping without active mapping should not work"""
    result = mock_main_runner.invoke(main, "from-mapping")
    assert result.exit_code == 1
    assert "No active mapping" in result.output


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
        "1234"
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
    """What if an error occurs halfway through?"""

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
    assert batch_folder.load().job_ids == ["1234"]


def test_show_set_default_parameters(mock_main_runner):
    # Try to run from-mapping
    mock_main_runner.get_context().settings.job_default_parameters = [
        Project("test_project"),
        DestinationPath("test_destination"),
    ]

    result = mock_main_runner.invoke(main, "show-defaults", catch_exceptions=False)
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
    # TODO: test_cli_create should use CreateCommandsContext by default in most tests
    mapping = CreateCommandsContext(
        context=mock_from_mapping_runner.mock_context
    ).get_mapping()

    def all_paths(mapping_in: Mapping):
        """List[str] of all paths in mapping"""
        return [
            str(x)
            for y in mapping_in.rows
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
    """Test dry run mode. Should not hit anything important"""

    result = mock_from_mapping_runner.invoke(
        main, "from-mapping --dry-run", input="Y", catch_exceptions=False
    )
    assert result.exit_code == 0
    assert "Dry run" in result.output
    assert "patient4" in result.output
    assert mock_requests_for_job_creation.requests.post.call_count == 0


def create_from_mapping_helper(
    root_source_path: str, destination_path: str, identifiers: List[SourceIdentifier]
):
    """Helper function that sets up a mapping to recreate #265"""
    return Mapping(
        options=[RootSourcePath(root_source_path), DestinationPath(destination_path)],
        grid=JobParameterGrid(
            rows=[[SourceIdentifierParameter(x) for x in identifiers]]
        ),
    )


def test_create_from_mapping_invalid_root_source(
    a_create_command_context, mock_requests_for_job_creation
):
    """The default mapping often contains a non-unc root source value, as a stand in
    until the user enters the actual unc path.
    If the mapping contains no path-based jobs then there should be no error
    Recreates #265
    """
    # The destination path is valid, but the root source is not.
    # there are no folder-based rows so root source is not needed
    mapping = create_from_mapping_helper(
        root_source_path="/not_unc",
        destination_path=r"\\proper\unc",
        identifiers=[
            StudyInstanceUIDIdentifierFactory(),
            StudyInstanceUIDIdentifierFactory(),
        ],
    )

    a_create_command_context.get_mapping = lambda: mapping
    runner = AnonAPIContextRunner(mock_context=a_create_command_context)
    result = runner.invoke(from_mapping, catch_exceptions=False)
    assert result.exit_code == 0  # this should not cause an issue

    # if there would be a path parameter in there though, it should cause
    # an issue because create a job with an invalid root should not happen
    mapping.grid.rows.append([SourceIdentifierParameter(FolderIdentifierFactory())])
    assert runner.invoke(from_mapping, catch_exceptions=False).exit_code == 1


def test_create_from_mapping_invalid_destination_path(
    a_create_command_context, mock_requests_for_job_creation
):
    """Companion to test_create_from_mapping_invalid_root_source. If there are no
    path jobs to be made, still make a problem if destination path is not valid
    Recreates #265
    """
    mapping = create_from_mapping_helper(
        root_source_path="/not_unc",
        destination_path=r"/also_not_unc",
        identifiers=[
            StudyInstanceUIDIdentifierFactory(),
            StudyInstanceUIDIdentifierFactory(),
        ],
    )

    a_create_command_context.get_mapping = lambda: mapping
    runner = AnonAPIContextRunner(mock_context=a_create_command_context)
    result = runner.invoke(from_mapping, catch_exceptions=False)
    assert result.exit_code == 1  # This run should not succeed


def test_create_from_mapping_folder_and_pacs(
    mock_from_mapping_runner,
    a_folder_with_mapping_diverse,
    mock_requests_for_job_creation,
):
    """PACS identifiers should generate slightly different jobs then Folder
    identifiers
    """
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
        "1234"
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
    with pytest.raises(JobSetValidationError):
        param_set.validate()


def test_job_parameter_set_validate_non_unc_paths(all_parameters):
    """Windows maps drive letters, makes then inaccessible to normal
    python code and then forbids using anything BUT drive letters in windows cmd
    A very annoying combination which makes it hard to determine what a path is
    in windows. Just make sure no jobs can be created with drive letters any paths
    """

    param_set = JobParameterSet(all_parameters)
    root_source = param_set.get_param_by_type(RootSourcePath)
    root_source.value = PureWindowsPath(r"Z:\folder1")
    with pytest.raises(JobSetValidationError):
        param_set.validate()


def test_job_parameter_set_fill_missing(all_parameters):
    """Make sure Pseudo ID and Pseudo Name have reasonable values"""

    assert fill_missing_test([PseudoID("an_id")]) == ("an_id", "an_id")
    assert fill_missing_test([PseudoName("a_name")]) == ("a_name", "a_name")
    assert fill_missing_test([PseudoName("a_name"), PseudoID("an_id")]) == (
        "an_id",
        "a_name",
    )
    param_set = JobParameterSet([])
    param_set.fill_missing_parameters()
    assert param_set.get_param_by_type(PseudoID) is None
    assert param_set.get_param_by_type(PseudoName) is None


def fill_missing_test(parameters: List[Parameter]) -> Tuple[str]:
    """Convenience function for testing job parameter fill missing"""
    param_set = JobParameterSet(parameters)
    param_set.fill_missing_parameters()
    return (
        param_set.get_param_by_type(PseudoID).value,
        param_set.get_param_by_type(PseudoName).value,
    )


def test_job_parameter_set_defaults():
    """You can set defaults for a parameter set. These are only kept if not
    overwritten
    """

    param_set = JobParameterSet(
        [PseudoID("1234"), PIMSKey("0000")],
        default_parameters=[Description("Default")],
    )
    assert param_set.get_param_by_type(Description).value == "Default"

    param_set2 = JobParameterSet(
        [PseudoID("1234"), Description("Overwrite!")],
        default_parameters=[Description("Default")],
    )
    assert param_set2.get_param_by_type(Description).value == "Overwrite!"


def test_create_from_mapping_syntax_error():
    """Trailing space in mapping should not be a problem.  Recreates #246"""

    # Set a mapping with an accession_number identifier that does not have expected
    # format
    mapping_path = RESOURCE_PATH / "test_cli_create" / "trailing_space_in_mapping.csv"

    # opening this should not raise an error
    with open(mapping_path, "r") as f:
        mapping = Mapping.load(f)
    # this trailing space should nog be in the parsed parameter. This will generate
    # a preventable error when trying to create a job with this
    assert not str(mapping.grid.rows[2][0]).endswith(" ")
