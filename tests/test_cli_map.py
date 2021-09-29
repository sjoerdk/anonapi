from pathlib import Path
from unittest.mock import Mock

from click.testing import CliRunner
from pytest import fixture


from anonapi.cli import entrypoint
from anonapi.cli.map_commands import (
    MapCommandContext,
    activate,
    add_accession_numbers,
    add_selection,
    delete,
    edit,
    find_dicom_files,
    add_study_folders,
    init,
    status,
)

from anonapi.mapper import (
    DEFAULT_MAPPING_NAME,
    Mapping,
    MappingFile,
    MappingLoadError,
)
from anonapi.parameters import ParameterSet, PseudoName, SourceIdentifierParameter
from anonapi.settings import DefaultAnonClientSettings
from tests.conftest import AnonAPIContextRunner, MockContextCliRunner
from tests import RESOURCE_PATH

MAPPER_RESOURCE_PATH = RESOURCE_PATH / "test_mapper"


class MappingContextRunner(AnonAPIContextRunner):
    """A click runner that always injects a MapCommandContext instance"""

    def __init__(self, mock_context: MapCommandContext):
        super().__init__(mock_context=mock_context)

    def get_current_mapping(self) -> Mapping:
        return self.mock_context.get_current_mapping()


@fixture
def mock_main_runner_with_mapping(mock_main_runner, a_folder_with_mapping):
    context = mock_main_runner.get_context()
    context.current_dir = lambda: NotImplementedError(
        "Call settings.active_mapping_file instead"
    )
    context.settings.active_mapping_file = a_folder_with_mapping / "anon_mapping.csv"
    return mock_main_runner


@fixture
def mock_map_context_with_mapping(a_folder_with_mapping) -> MapCommandContext:
    return MapCommandContext(
        current_dir=a_folder_with_mapping,
        settings=DefaultAnonClientSettings(
            active_mapping_file=a_folder_with_mapping / "anon_mapping.csv"
        ),
    )


@fixture
def runner_with_mapping(mock_map_context_with_mapping) -> MappingContextRunner:
    """A click CLIRunner with MapCommandContext that has a valid active mapping"""
    return MappingContextRunner(mock_context=mock_map_context_with_mapping)


@fixture
def mock_map_context_without(tmpdir) -> MapCommandContext:
    return MapCommandContext(current_dir=tmpdir, settings=DefaultAnonClientSettings(),)


@fixture
def runner_without_mapping(tmpdir):
    """A click CLIRunner that passes MapCommandContext without active mapping
    (active mapping is None)
    """
    return MockContextCliRunner(
        mock_context=MapCommandContext(
            current_dir=tmpdir, settings=DefaultAnonClientSettings()
        )
    )


def test_cli_map_add_selection(
    runner_with_mapping, a_folder_with_mapping_and_fileselection
):
    """Add a file selection to a mapping."""
    mapping_folder, fileselection_path = a_folder_with_mapping_and_fileselection

    runner = runner_with_mapping
    result = runner.invoke(
        add_selection, str(fileselection_path), catch_exceptions=False
    )
    assert result.exit_code == 0

    mapping = runner_with_mapping.mock_context.get_current_mapping()
    assert len(mapping) == 21
    assert "fileselection:a_folder/a_file_selection.txt" in "".join(
        [str(x) for y in mapping.rows for x in y]
    )


def test_cli_map(mock_main_runner, mock_cli_base_context, tmpdir):
    result = mock_main_runner.invoke(entrypoint.cli, "map init", catch_exceptions=False)
    with open(Path(tmpdir) / "anon_mapping.csv", "r") as f:
        f.read()

    assert result.exit_code == 0


def test_cli_map_init(mock_main_runner, tmpdir):
    runner = mock_main_runner

    #  there should be no mapping to start with
    assert (
        "Could not find mapping"
        in runner.invoke(entrypoint.cli, "map activate", catch_exceptions=False).output
    )

    # but after init there should be a valid mapping
    runner.invoke(entrypoint.cli, "map init", catch_exceptions=False)
    mapping_path = mock_main_runner.get_context().current_dir / DEFAULT_MAPPING_NAME
    assert mapping_path.exists()
    MappingFile(mapping_path).load_mapping()  # should not crash

    # and the created mapping should have been activated
    assert mock_main_runner.get_context().settings.active_mapping_file == mapping_path


def test_cli_map_info(mock_main_runner_with_mapping):
    """Running map info should give you a nice print of contents"""
    context = mock_main_runner_with_mapping.get_context()
    context.current_dir = RESOURCE_PATH / "test_cli"

    runner = mock_main_runner_with_mapping
    result = runner.invoke(entrypoint.cli, "map status", catch_exceptions=False)

    assert result.exit_code == 0
    assert "folder:folder/file4  patientName4" in result.output


def test_cli_map_info_empty_dir(mock_main_runner):
    """Running info on a directory not containing a mapping file should yield a
    nice 'no mapping' message
    """
    runner = mock_main_runner
    result = runner.invoke(entrypoint.cli, "map status", catch_exceptions=False)

    assert result.exit_code == 1
    assert "No active mapping" in result.output


def test_cli_map_info_no_active_mapping(runner_without_mapping):
    """Running info on a directory not containing a mapping file should yield a
    nice 'no mapping' message
    """

    result = runner_without_mapping.invoke(status, catch_exceptions=False)

    assert result.exit_code == 1
    assert "No active mapping" in result.output


def test_cli_map_info_load_exception(mock_main_runner, monkeypatch):
    """Running info with a corrupt mapping file should yield a nice message"""
    # make sure a valid mapping file is found
    context = mock_main_runner.get_context()
    context.settings.active_mapping_file = (
        RESOURCE_PATH / "test_cli" / "anon_mapping.csv"
    )

    # but then raise exception when loading
    def mock_load(x):
        raise MappingLoadError("Test Exception")

    monkeypatch.setattr("anonapi.mapper.JobParameterGrid.load", mock_load)
    runner = CliRunner()

    result = runner.invoke(entrypoint.cli, "map status", catch_exceptions=False)

    assert result.exit_code == 1
    assert "Test Exception" in result.output


def test_cli_map_add_folder(mock_map_context_without, folder_with_some_dicom_files):
    """Add all dicom files in this folder to mapping"""
    context = mock_map_context_without
    runner = AnonAPIContextRunner(mock_context=context)
    selection_folder = folder_with_some_dicom_files

    # Add this folder to mapping
    result = runner.invoke(
        add_study_folders, args=[str(selection_folder.path)], catch_exceptions=False,
    )

    # oh no! no mapping yet!
    assert "No active mapping" in result.output

    # make one
    runner.invoke(init)
    # by default there are no rows mapping
    assert len(context.get_current_mapping().grid) == 0

    # No selection file has been put in the folder at this point
    assert not selection_folder.has_file_selection()

    # but after adding
    result = runner.invoke(
        add_study_folders, args=[str(selection_folder.path)], catch_exceptions=False
    )

    # There should be a selection there
    assert result.exit_code == 0
    assert selection_folder.has_file_selection()

    # also, this selection should have been added to the mapping:
    mapping = context.get_current_mapping()  # reload from disk
    assert len(mapping.grid) == 1
    added = ParameterSet(mapping.grid.rows[-1])
    identifier = added.get_param_by_type(SourceIdentifierParameter)
    # and the identifier should be a FileSelectionIdentifier which is
    # relative to the current path
    assert not identifier.path.is_absolute()


def test_cli_map_add_folder_no_check(
    mock_map_context_without, folder_with_some_dicom_files
):
    """Add all dicom files in this folder to mapping but do not scan"""
    context = mock_map_context_without
    runner = AnonAPIContextRunner(mock_context=context)
    selection_folder = folder_with_some_dicom_files

    runner.invoke(init)
    # by default there are no rows
    assert len(context.get_current_mapping().grid) == 0

    # dicom files should not have been selected yet currently
    assert not selection_folder.has_file_selection()

    # but after adding
    result = runner.invoke(
        add_study_folders,
        args=["--no-check-dicom", str(selection_folder.path)],
        catch_exceptions=False,
    )

    # There should be a selection there
    assert result.exit_code == 0
    assert selection_folder.has_file_selection()
    assert "that look like DICOM" in result.output


@fixture
def create_fileselection_click_recorder(monkeypatch):
    """Add a decorator around the function that adds paths to mapping. Function
    will still works as normal, but calls are recorded
    """

    recorder = Mock()

    def find_dicom_files_recorded(*args, **kwargs):
        """Run the original function, but track calls"""
        recorder(*args, **kwargs)
        return find_dicom_files(*args, **kwargs)

    monkeypatch.setattr(
        "anonapi.cli.map_commands.find_dicom_files", find_dicom_files_recorded,
    )
    return recorder


def test_cli_map_add_study_folders(
    runner_with_mapping,
    folder_with_mapping_and_some_dicom_files,
    create_fileselection_click_recorder,
    monkeypatch,
):
    """Add multiple study folders using the add-study-folders command"""
    context: MapCommandContext = runner_with_mapping.mock_context
    context.current_dir = folder_with_mapping_and_some_dicom_files.path
    monkeypatch.setattr(
        "os.getcwd", lambda: str(folder_with_mapping_and_some_dicom_files.path)
    )

    result = runner_with_mapping.invoke(
        add_study_folders, args=["--no-check-dicom", "*"], catch_exceptions=False,
    )

    assert create_fileselection_click_recorder.call_count == 2
    assert "that look like DICOM" in result.output


def test_cli_map_delete(mock_map_context_with_mapping):
    """Running map info should give you a nice print of contents"""
    context = mock_map_context_with_mapping
    runner = AnonAPIContextRunner(mock_context=context)

    assert context.settings.active_mapping_file.exists()

    result = runner.invoke(delete, catch_exceptions=False)
    assert result.exit_code == 0
    assert not context.settings.active_mapping_file.exists()

    # deleting again will yield nice message
    result = runner.invoke(delete)
    assert result.exit_code == 1
    assert "No such file or directory" in result.output


def test_cli_map_edit(mock_map_context_with_mapping, mock_launch):
    context = mock_map_context_with_mapping
    runner = AnonAPIContextRunner(mock_context=context)

    result = runner.invoke(edit, catch_exceptions=False)

    assert result.exit_code == 0
    assert mock_launch.called

    # now try edit without any mapping being present
    mock_launch.reset_mock()
    runner.invoke(delete)
    result = runner.invoke(edit)

    assert "No mapping file found at" in result.output
    assert not mock_launch.called


def test_cli_map_activate(mock_map_context_with_mapping):
    context = mock_map_context_with_mapping
    runner = AnonAPIContextRunner(mock_context=context)
    settings = context.settings

    settings.active_mapping_file = None  # we start with a mapping file, but no active

    # after activating, active mapping should be set
    runner.invoke(activate)
    assert settings.active_mapping_file == context.current_dir / "anon_mapping.csv"

    # Graceful error when activating when there is no mapping in current dir
    runner.invoke(delete)
    assert "Could not find mapping file at" in runner.invoke(activate).output


def test_cli_map_add_paths_file(
    mock_map_context_with_mapping, folder_with_some_dicom_files, monkeypatch
):
    """Add an xls file containing several paths and potentially pseudonyms
    to an existing mapping
    """
    context = mock_map_context_with_mapping
    runner = AnonAPIContextRunner(mock_context=context)

    # assert mapping is as expected
    mapping = context.get_current_mapping()
    assert len(mapping.grid) == 20

    # now try to add something from the directory with some dicom files
    context.current_dir = folder_with_some_dicom_files.path
    monkeypatch.setattr("os.getcwd", lambda: folder_with_some_dicom_files.path)

    folders = [
        x for x in folder_with_some_dicom_files.path.glob("*") if not x.is_file()
    ]

    # First run with regular command line input
    result = runner.invoke(
        add_study_folders, args=[str(folders[0])], catch_exceptions=False
    )
    assert result.exit_code == 0

    # Then run with input file input (input file contains 2 folders + names)
    input_file_path = MAPPER_RESOURCE_PATH / "inputfile" / "some_folder_names.xlsx"
    result = runner.invoke(
        add_study_folders, args=["-f", str(input_file_path)], catch_exceptions=False
    )
    assert result.exit_code == 0

    # now three rows should have been added
    added = context.get_current_mapping().grid.rows[20:]
    assert len(added) == 3

    # and the pseudo names from the input file should have been included
    pseudo_names = [ParameterSet(x).get_param_by_type(PseudoName) for x in added]
    assert pseudo_names[1].value == "studyA"
    assert pseudo_names[2].value == "studyB"


def test_cli_map_add_accession_numbers(runner_with_mapping):
    """Add some accession numbers to a mapping"""
    result = runner_with_mapping.invoke(add_accession_numbers, ["12344556.12342345"])
    assert result.exit_code == 0
    mapping = runner_with_mapping.get_current_mapping()
    # TODO: make accessing a specific parameter in a row easier. Not like below.
    assert (
        ParameterSet(mapping.rows[-1]).as_dict()["source"].value.identifier
        == "12344556.12342345"
    )


def test_cli_map_add_accession_numbers_file(runner_with_mapping):
    """Add some accession numbers to a mapping"""

    input_file_path = MAPPER_RESOURCE_PATH / "inputfile" / "some_accession_numbers.xlsx"
    result = runner_with_mapping.invoke(
        add_accession_numbers, ["--input-file", str(input_file_path)]
    )
    assert result.exit_code == 0
    mapping = runner_with_mapping.get_current_mapping()
    assert (
        ParameterSet(mapping.rows[-1]).as_dict()["source"].value.identifier
        == "123456.12321313"
    )
    assert ParameterSet(mapping.rows[-1]).as_dict()["pseudo_name"].value == "study3"
