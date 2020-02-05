import pytest
from click.exceptions import BadParameter

from anonapi.cli.click_types import FileSelectionFileParam
from tests import RESOURCE_PATH


@pytest.fixture
def test_resources():
    return RESOURCE_PATH / "test_cli_click_types"


def test_file_selection_file(test_resources):
    """Test loading of fileselection when OK or when file is missing or corrupt"""
    param = FileSelectionFileParam()
    with pytest.raises(BadParameter):
        param.convert(value="non_existent", param=None, ctx=None)

    with pytest.raises(BadParameter):
        param.convert(
            value=str(test_resources / "corruptfileselection.txt"), param=None, ctx=None
        )

    selection = param.convert(
        value=str(test_resources / "fileselection.txt"), param=None, ctx=None
    )
    assert len(selection.selected_paths) == 3
