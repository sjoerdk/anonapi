import pytest

from anonapi.inputfile import (
    FolderColumn,
    InputFileException,
    extract_parameter_grid,
)
from tests import RESOURCE_PATH


def test_extract_parameter_grid_simple():
    """Parse parameters from a simple xls file with two rows and some comments
    at the top
    """
    input_file = RESOURCE_PATH / "test_inputfile" / "example_deid_form.xlsx"
    grid = extract_parameter_grid(input_file)
    assert [str(x) for x in grid.rows[0]] == [
        "accession_number,1234567.12345678",
        "pseudo_name,patient1",
    ]
    assert [str(x) for x in grid.rows[1]] == [
        "accession_number,2234567.12345679",
        "pseudo_name,patient2",
    ]


def test_extract_parameter_grid_errors():
    """Tese a few situations that should raise errors"""

    input_file = (
        RESOURCE_PATH / "test_inputfile" / "example_deid_form_missing_values.xlsx"
    )
    with pytest.raises(InputFileException):
        extract_parameter_grid(input_file)


def test_extract_paths():
    """Parse a list of paths"""

    input_file = RESOURCE_PATH / "test_inputfile" / "some_folder_names.xlsx"
    grid = extract_parameter_grid(input_file, column_types=[FolderColumn])

    assert len(grid.rows) == 3  # this should be three rows
    assert len(grid.rows[0]) == 1  # should just have picked up path, not other column
    assert [str(row[0].path) for row in grid.rows] == [
        r"Kees\01",
        r"Henk\10",
        r"Kees\02",
    ]


def test_find_no_parameters():
    """When no column can be found, exceptions should be raised"""
    input_file = (
        RESOURCE_PATH / "test_inputfile" / "example_deid_form_missing_values.xlsx"
    )

    with pytest.raises(InputFileException):
        # FolderColumn is not present in this file
        extract_parameter_grid(input_file, column_types=[FolderColumn])
