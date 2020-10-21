import os

import pytest
from click.exceptions import BadParameter

from anonapi.cli.click_parameter_types import (
    AccessionNumberFile,
    PathParameterFile,
    TabularParameterFile,
    WildcardFolder,
)
from tests import RESOURCE_PATH


@pytest.fixture
def test_cli_param_dir():
    old_cwd = os.getcwd()
    os.chdir(RESOURCE_PATH / "test_cli_parameters")
    yield
    os.chdir(old_cwd)


@pytest.mark.parametrize(
    "value,expected_len",
    [
        ("*", 3),
        ("*A", 1),
        ("folder1*", 2),
        ("folder1A", 1),
        ("*/subfolder*", 3),
        ("nonexistant/*", 0),
    ],
)
def test_acceptable_wildcards(test_cli_param_dir, value, expected_len):
    """Wildcard folder will accept single folder names and expand any wildcards"""
    output = WildcardFolder().convert(value=value, param=None, ctx=None)
    assert len(output) == expected_len


def test_tabular_parameter_file():
    """Custom parameter that takes a path to a tabular file with parameters and
    parses this to a parameter grid
    """

    tabular_parameter_file = (
        RESOURCE_PATH / "test_cli_click_types" / "some_folder_names.xlsx"
    )

    # Click documentation states that Types should pass through None unaltered
    assert TabularParameterFile().convert(None, param=None, ctx=None) is None

    # basic usage. This should parse the file
    converted = PathParameterFile().convert(
        value=str(tabular_parameter_file), param=None, ctx=None
    )
    assert len(converted.rows) == 3


def test_tabular_parameter_file_errors():
    tabular_parameter_file = (
        RESOURCE_PATH / "test_cli_click_types" / "some_folder_names.xlsx"
    )

    # test failing if required columns are not found in file
    with pytest.raises(BadParameter):
        AccessionNumberFile().convert(
            value=str(tabular_parameter_file), param=None, ctx=None
        )

    # test nonsensical path
    with pytest.raises(BadParameter):
        AccessionNumberFile().convert(
            value="/doesnotexist/really", param=None, ctx=None
        )
    # test non_existing file
    with pytest.raises(BadParameter):
        AccessionNumberFile().convert(value="/doesnotexist.xlsx", param=None, ctx=None)
