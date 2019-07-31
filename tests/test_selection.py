import pytest

from anonapi.selection import SelectionFolder, SelectionFolderFileList, InconsistentDICOM
from tests import RESOURCE_PATH


def test_selection_tool():
    test_dir = RESOURCE_PATH / "test_selection" / "test_dir"
    tool = SelectionFolder(test_dir)

    files = tool.get_all_file_paths(test_dir)
    checklist = SelectionFolderFileList(files)

    for _ in checklist:
        pass
    dicom_files = checklist.paths_selected

    assert len(files) == 6
    assert len(dicom_files) == 3


def test_selection_tool():
    """Different patientIDs should raise exceptions
    """
    test_dir = RESOURCE_PATH / "test_selection" / "test_dir_different_patientID"
    tool = SelectionFolder(test_dir)

    files = tool.get_all_file_paths(test_dir)
    checklist = SelectionFolderFileList(files)
    with pytest.raises(InconsistentDICOM) as e:
        [_ for _ in checklist]
    assert 'PatientID' in str(e)

    # check also for studyInstanceUID
    files = tool.get_all_file_paths(test_dir / '2.0-CT-1')
    checklist = SelectionFolderFileList(files)
    with pytest.raises(InconsistentDICOM) as e:
        [_ for _ in checklist]
    assert 'StudyInstanceUID' in str(e)
