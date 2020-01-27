import pytest

from anonapi.selection import FileFolder, open_as_dicom
from tests import RESOURCE_PATH


@pytest.fixture()
def a_file_folder():
    return FileFolder(RESOURCE_PATH / "test_selection" / "test_dir")


def test_selection_tool(a_file_folder):

    files = list(a_file_folder.iterate())
    assert len(files) == 5
    assert len([x for x in files if open_as_dicom(x)]) == 3


def test_selection_tool_parameters(a_file_folder):
    """Try out different iteration parameters FileFolder"""

    folder = a_file_folder

    def assert_len(iterator, expected_len):
        assert len(list(iterator)) == expected_len

    assert_len(folder.iterate(), 5)
    assert_len(folder.iterate(ignore_dotfiles=False), 6)
    assert_len(folder.iterate(pattern="1"), 2)
    assert_len(folder.iterate(pattern="*.txt"), 1)
    assert "somedoc.odt" in str(list(folder.iterate(pattern="*", recurse=False))[0])
    assert_len(folder.iterate(pattern="*", exclude_patterns=["2.0*"]), 3)
    assert_len(folder.iterate(pattern="*", exclude_patterns=["2.0*", "AiCE*"]), 2)
    assert_len(folder.iterate(pattern="*.*", exclude_patterns=["2.0*", "AiCE*"]), 1)
    assert_len(folder.iterate(pattern='*', exclude_patterns=['*/some*']), 4)
