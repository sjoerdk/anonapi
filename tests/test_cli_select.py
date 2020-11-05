"""Tests for anonapi.cli.select_commands"""
from pathlib import Path

import pytest
from fileselection.fileselection import FileSelectionFolder, FileSelectionFile
from anonapi.cli.select_commands import main, SelectCommandContext, CLIMessages
from anonapi.selection import looks_like_dicom_file


@pytest.fixture()
def mock_selection_folder(tmpdir):
    """Selection Folder without any selection"""
    selection_folder = FileSelectionFolder(path=tmpdir)
    return selection_folder


@pytest.fixture()
def initialised_selection_folder(mock_selection_folder):
    """Will seed the default 'current' folder with a selection"""
    rootpath = mock_selection_folder.path
    selection = FileSelectionFile(
        data_file_path=mock_selection_folder.get_data_file_path(),
        description="mock_selection_for_testing",
        selected_paths=[
            rootpath / "root_path" / "file1",
            rootpath / "root_path" / "file2",
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


def test_select_add(mock_main_runner, folder_with_some_dicom_files):
    selection_folder = folder_with_some_dicom_files
    mock_main_runner.set_mock_current_dir(selection_folder.path)

    assert not selection_folder.has_file_selection()
    result = mock_main_runner.invoke(main, args=["add", "*"], catch_exceptions=False)
    assert result.exit_code == 0


def test_select_add_append(mock_main_runner, folder_with_some_dicom_files):
    """Running add twice should add only new paths"""
    selection_folder = folder_with_some_dicom_files
    mock_main_runner.set_mock_current_dir(selection_folder.path)

    # start with emtpy selection and add a file
    assert not selection_folder.has_file_selection()
    mock_main_runner.invoke(main, args=["add", "*.txt"], catch_exceptions=False)
    assert len(selection_folder.load_file_selection().selected_paths) == 1

    # now add the same file again
    mock_main_runner.invoke(main, args=["add", "*.txt"], catch_exceptions=False)
    # this should not have added any new file because it was already there
    assert len(selection_folder.load_file_selection().selected_paths) == 1
    # now add more
    mock_main_runner.invoke(main, args=["add", "1"], catch_exceptions=False)
    assert len(selection_folder.load_file_selection().selected_paths) == 3


def test_select_add_exclude(mock_main_runner, folder_with_some_dicom_files):
    """Running add twice should add only new paths"""
    selection_folder = folder_with_some_dicom_files
    mock_main_runner.set_mock_current_dir(selection_folder.path)

    # start with emtpy selection and add a file
    assert not selection_folder.has_file_selection()
    mock_main_runner.invoke(main, args=["add", "1"], catch_exceptions=False)
    assert len(selection_folder.load_file_selection().selected_paths) == 2

    mock_main_runner.invoke(main, args=["delete"], catch_exceptions=False)
    assert not selection_folder.has_file_selection()

    mock_main_runner.invoke(
        main,
        args="add * --exclude-pattern 2.0* --exclude-pattern *1".split(" "),
        catch_exceptions=False,
    )
    assert len(selection_folder.load_file_selection().selected_paths) == 2


def test_select_edit(mock_main_runner, initialised_selection_folder, mock_launch):

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


@pytest.mark.parametrize(
    "path",
    [
        "./file1.dcm",
        "file2.dcm",
        "long.file.name_.dicom",
        "1232.3.4.43.5",
        "RAW134.234.2353555",
        "RAW134.234.2353555.123",
        Path(r"D:\something\file2.dicom"),
        "1",
        "/path/lotsoflettersnonumbers",  # might be a dicom file?
        "/path/thing/2",
    ],
)
def test_looks_like_dicom_true(path):
    """These should all be recognized as DICOM files"""
    assert looks_like_dicom_file(path)


@pytest.mark.parametrize(
    "path", ["/path/thing/info.xml", "dicom.txt", "foo.doc", Path(r"C:\athing.txt")]
)
def test_looks_like_dicom_false(path):
    """These should all be seen as non DICOM files"""
    assert not looks_like_dicom_file(path)
