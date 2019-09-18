import pytest

from anonapi.selection import DICOMFileFolder
from tests import RESOURCE_PATH


def test_selection_tool():
    test_dir = RESOURCE_PATH / "test_selection" / "test_dir"

    folder = DICOMFileFolder(test_dir)
    files = [x for x in folder.all_files() if x is not None]
    dicom_files = [x[0] for x in folder.all_dicom_files(files) if x[1] is not None]

    assert len(folder.all_dicom_files(files)) == 6
    assert len(files) == 6
    assert len(dicom_files) == 3
