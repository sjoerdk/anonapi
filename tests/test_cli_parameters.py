import os

import pytest

from anonapi.cli.click_parameters import WildcardFolder
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
