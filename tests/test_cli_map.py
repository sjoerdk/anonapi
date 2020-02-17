from pathlib import Path, PureWindowsPath
from unittest.mock import Mock

from click.testing import CliRunner
from pytest import fixture


from anonapi.cli import entrypoint
from anonapi.cli.map_commands import (
    MapCommandContext,
    add_selection,
    add_all_study_folders,
    add_path_to_mapping_click,
)
from anonapi.mapper import MappingLoadError, MappingFolder
from anonapi.parameters import ParameterSet, RootSourcePath, SourceIdentifierParameter
from anonapi.settings import DefaultAnonClientSettings
from tests.conftest import MockContextCliRunner
from tests import RESOURCE_PATH


@fixture
def mock_main_runner_with_mapping(mock_main_runner, a_folder_with_mapping):
    mock_main_runner.get_context().current_dir = a_folder_with_mapping
    return mock_main_runner


@fixture
def map_command_runner_mapping_dir(a_folder_with_mapping):
    """A click CLIRunner that MapCommandContext pointing to a dir with some mapping
    """
    return MockContextCliRunner(
        mock_context=MapCommandContext(
            current_path=a_folder_with_mapping, settings=DefaultAnonClientSettings()
        )
    )


def test_cli_map_add_selection(
    map_command_runner_mapping_dir, a_folder_with_mapping_and_fileselection
):
    """Add a file selection to a mapping."""
    mapping_folder, fileselection_path = a_folder_with_mapping_and_fileselection

    runner = map_command_runner_mapping_dir
    result = runner.invoke(
        add_selection, str(fileselection_path), catch_exceptions=False
    )
    assert result.exit_code == 0

    mapping = map_command_runner_mapping_dir.mock_context.get_current_mapping()
    assert len(mapping) == 21
    assert "fileselection:a_folder/a_file_selection.txt" in "".join(
        [str(x) for y in mapping.rows() for x in y]
    )


def test_cli_map(mock_main_runner, mock_cli_base_context, tmpdir):
    result = mock_main_runner.invoke(entrypoint.cli, "map init", catch_exceptions=False)
    with open(Path(tmpdir) / "anon_mapping.csv", "r") as f:
        content = f.read()

    assert result.exit_code == 0


def test_cli_map_init(mock_main_runner, mock_cli_base_context, tmpdir):
    result = mock_main_runner.invoke(entrypoint.cli, "map init", catch_exceptions=False)
    assert result.exit_code == 0
    assert MappingFolder(folder_path=Path(tmpdir)).has_mapping()
    # getting this mapping should not crash
    mapping = MappingFolder(folder_path=Path(tmpdir)).get_mapping()

    # the base source should have been set to the current dir
    param_set = ParameterSet(mapping.options)
    root_source_path = param_set.get_param_by_type(RootSourcePath)
    assert root_source_path.value == PureWindowsPath(tmpdir)


def test_cli_map_info(mock_main_runner_with_mapping):
    """running map info should give you a nice print of contents"""
    context = mock_main_runner_with_mapping.get_context()
    context.current_dir = RESOURCE_PATH / "test_cli"

    runner = mock_main_runner_with_mapping
    result = runner.invoke(entrypoint.cli, "map status", catch_exceptions=False)

    assert result.exit_code == 0
    assert "file16/nogiets" in result.output


def test_cli_map_info_empty_dir(mock_main_runner):
    """running info on a directory not containing a mapping file should yield a
    nice 'no mapping' message"""
    runner = mock_main_runner
    result = runner.invoke(entrypoint.cli, "map status")

    assert result.exit_code == 1
    assert "No mapping defined" in result.output


def test_cli_map_info_load_exception(mock_main_runner, monkeypatch):
    """running info with a corrupt mapping file should yield a nice message"""
    # make sure a valid mapping file is found
    context = mock_main_runner.get_context()
    context.current_dir = str(RESOURCE_PATH / "test_cli")

    # but then raise exception when loading
    def mock_load(x):
        raise MappingLoadError("Test Exception")

    monkeypatch.setattr("anonapi.mapper.JobParameterGrid.load", mock_load)
    runner = CliRunner()

    result = runner.invoke(entrypoint.cli, "map status")

    assert result.exit_code == 1
    assert "Test Exception" in result.output


def test_cli_map_add_folder(mock_main_runner, folder_with_some_dicom_files):
    """Add all dicom files in this folder to mapping"""
    selection_folder = folder_with_some_dicom_files

    # Add this folder to mapping
    result = mock_main_runner.invoke(
        entrypoint.cli,
        f"map add-study-folder {selection_folder.path}",
        catch_exceptions=False,
    )

    # oh no! no mapping yet!
    assert "No mapping defined in current" in result.output

    # make one
    mock_main_runner.invoke(entrypoint.cli, f"map init")
    mapping_folder = MappingFolder(mock_main_runner.mock_context.current_dir)
    assert (
        len(mapping_folder.load_mapping().grid) == 4
    )  # by default there are 4 example rows in mapping

    # dicom files should not have been selected yet currently
    assert not selection_folder.has_file_selection()
    result = mock_main_runner.invoke(
        entrypoint.cli, f"map add-study-folder {selection_folder.path}"
    )
    # but should be now
    assert result.exit_code == 0
    assert selection_folder.has_file_selection()

    # also, this selection should have been added to the mapping:
    mapping = mapping_folder.load_mapping()  # reload from disk
    assert len(mapping.grid) == 5
    added = ParameterSet(mapping.grid.rows[-1])
    identifier = added.get_param_by_type(SourceIdentifierParameter)
    # and the identifier should be a FileSelectionIdentifier which is
    # relative to the current path
    assert not identifier.path.is_absolute()


@fixture
def add_path_to_mapping_click_recorder(monkeypatch):
    """Add a decorator around the function that adds paths to mapping. Function
    will still works as normal, but calls are recorded"""

    recorder = Mock()

    def add_path_to_mapping_click_recorded(*args, **kwargs):
        """Run the original function, but track calls"""
        recorder(*args, **kwargs)
        return add_path_to_mapping_click(*args, **kwargs)

    monkeypatch.setattr(
        "anonapi.cli.map_commands.add_path_to_mapping_click",
        add_path_to_mapping_click_recorded,
    )
    return recorder


def test_cli_map_add_all_study_folders(
    map_command_runner_mapping_dir,
    folder_with_mapping_and_some_dicom_files,
    add_path_to_mapping_click_recorder,
    monkeypatch,
):
    """Add multiple study folders"""
    context: MapCommandContext = map_command_runner_mapping_dir.mock_context
    context.current_path = folder_with_mapping_and_some_dicom_files.path
    monkeypatch.setattr(
        "os.getcwd", lambda: str(folder_with_mapping_and_some_dicom_files.path)
    )

    # Add this folder to mapping, but cancel
    result = map_command_runner_mapping_dir.invoke(
        add_all_study_folders, f"{'*'}", input="No", catch_exceptions=False,
    )
    # nothing should have been done
    assert result.exit_code == 0
    assert "Cancelled" in result.output
    assert not add_path_to_mapping_click_recorder.called

    # now repeat and do not cancel
    result = map_command_runner_mapping_dir.invoke(
        add_all_study_folders, f"{'*'}", input="Yes", catch_exceptions=False,
    )

    assert add_path_to_mapping_click_recorder.call_count == 2


def test_cli_map_delete(mock_main_runner, a_folder_with_mapping):
    """running map info should give you a nice print of contents"""
    mock_main_runner.set_mock_current_dir(a_folder_with_mapping)

    mapping_folder = MappingFolder(a_folder_with_mapping)
    assert mapping_folder.has_mapping()

    result = mock_main_runner.invoke(
        entrypoint.cli, "map delete", catch_exceptions=False
    )

    assert result.exit_code == 0
    assert not mapping_folder.has_mapping()

    # deleting  again will yield nice message
    result = mock_main_runner.invoke(entrypoint.cli, "map delete")
    assert result.exit_code == 1
    assert "No mapping defined" in result.output


def test_cli_map_edit(mock_main_runner_with_mapping, monkeypatch):
    mock_launch = Mock()
    monkeypatch.setattr("anonapi.cli.select_commands.click.launch", mock_launch)

    runner = mock_main_runner_with_mapping
    result = runner.invoke(entrypoint.cli, "map edit")

    assert result.exit_code == 0
    assert mock_launch.called

    # now try edit without any mapping being present
    mock_launch.reset_mock()
    runner.invoke(entrypoint.cli, "map delete")
    result = runner.invoke(entrypoint.cli, "map edit")

    assert result.exit_code == 0
    assert "No mapping file defined" in result.output
    assert not mock_launch.called
