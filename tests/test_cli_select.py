"""Tests for anonapi.cli.select_commands"""
from unittest.mock import Mock

import pytest
from fileselection.fileselection import FileSelectionFolder, FileSelectionFile

from anonapi.cli.parser import AnonCommandLineParser
from anonapi.cli.select_commands import main, SelectCommandContext, CLIMessages
from tests.conftest import AnonCommandLineParserRunner


@pytest.fixture()
def mock_selection_folder(tmpdir):
    """Selection Folder without any selection"""
    selection_folder = FileSelectionFolder(path=tmpdir)
    return selection_folder


@pytest.fixture()
def initialised_selection_folder(mock_selection_folder):
    """Will seed the default 'current' folder with a selection """
    rootpath = mock_selection_folder.path
    selection = FileSelectionFile(
        data_file_path=mock_selection_folder.get_data_file_path(),
        description="mock_selection_for_testing",
        selected_paths=[
            rootpath / "path" / "file1",
            rootpath / "path" / "file2",
            rootpath / "path2" / "file1",
            rootpath / "path3" / "subdir" / "file1",
        ],
    )
    mock_selection_folder.save_file_selection(selection)
    return mock_selection_folder


@pytest.fixture()
def mock_selection_context(mock_selection_folder):
    """Context required by all select commands"""
    return SelectCommandContext(current_path=mock_selection_folder.path)


@pytest.fixture()
def mock_cli_parser(mock_selection_folder):
    """Context required only by select_commands.main. Will yield a temp folder as current_dir()"""
    parser = AnonCommandLineParser(client_tool=Mock(), settings=Mock())
    parser.current_dir = lambda: mock_selection_folder.path
    return parser


@pytest.fixture()
def mock_main_runner(mock_cli_parser):
    """a click.testing.CliRunner that always passes a mocked context to any call, making sure any operations
    on current dir are done in a temp folder"""
    runner = AnonCommandLineParserRunner(mock_context=mock_cli_parser)
    return runner


def test_select_status(mock_main_runner, initialised_selection_folder):
    result = mock_main_runner.invoke(main, "status")

    assert "containing 4 files" in result.output
    assert "mock_selection_for_testing" in result.output


def test_select_delete(mock_main_runner, initialised_selection_folder):
    assert initialised_selection_folder.has_file_selection()
    result = mock_main_runner.invoke(main, "delete")
    assert result.exit_code == 0
    assert not initialised_selection_folder.has_file_selection()

    # removing when there is no will yield a helpful message
    result = mock_main_runner.invoke(main, "delete")
    assert "There is no selection defined" in result.output


def test_select_create(mock_main_runner, folder_with_some_dicom_files):
    selection_folder = folder_with_some_dicom_files
    mock_main_runner.set_mock_current_dir(selection_folder.path)

    assert not selection_folder.has_file_selection()
    result = mock_main_runner.invoke(main, "create")
    assert result.exit_code == 0
    assert selection_folder.has_file_selection()
    assert "Found 3 DICOM files" in result.output


def test_select_edit(mock_main_runner, initialised_selection_folder, monkeypatch):
    mock_launch = Mock()
    monkeypatch.setattr("anonapi.cli.select_commands.click.launch", mock_launch)

    result = mock_main_runner.invoke(main, "edit")
    assert result.exit_code == 0
    assert mock_launch.called

    mock_launch.reset_mock()
    # now if the selection is removed
    mock_main_runner.invoke(main, "delete")
    # you cannot edit anymore
    result = mock_main_runner.invoke(main, "edit")
    assert CLIMessages.NO_SELECTION_DEFINED in result.output
    assert not mock_launch.called
