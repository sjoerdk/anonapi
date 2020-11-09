import pytest

from anonapi.inputfile import (
    AccessionNumberColumn,
    ExcelFile,
    FolderColumn,
    InputFileException,
    PseudonymColumn,
    as_tabular_file,
    extract_parameter_grid,
)
from tests import RESOURCE_PATH


LOCAL_RESOURCE_PATH = RESOURCE_PATH / "test_inputfile"
FORMATS_PATH = LOCAL_RESOURCE_PATH / "formats"


def test_extract_parameter_grid_simple():
    """Parse parameters from a simple xls file with two rows and some comments
    at the top
    """
    input_file = ExcelFile(LOCAL_RESOURCE_PATH / "example_deid_form.xlsx")
    grid = extract_parameter_grid(input_file)

    assert [str(x) for x in grid.rows[0]] == [
        "accession_number,1234567.12345678",
        "pseudo_name,patient1",
    ]
    assert [str(x) for x in grid.rows[1]] == [
        "accession_number,2234567.12345679",
        "pseudo_name,patient2",
    ]


def test_extract_parameter_grid_required():
    """You can pass column types that must be found, otherwise error"""

    input_file = ExcelFile(LOCAL_RESOURCE_PATH / "example_deid_form.xlsx")
    with pytest.raises(InputFileException):
        # file does not contain a 'folder' column. Requiring this should fail
        extract_parameter_grid(
            input_file,
            optional_column_types=[AccessionNumberColumn, PseudonymColumn],
            required_column_types=[FolderColumn],
        )

    # without requiring, missing column should not be a problem
    extract_parameter_grid(
        input_file,
        optional_column_types=[FolderColumn, AccessionNumberColumn, PseudonymColumn],
        required_column_types=[],
    )

    # This is dumb but possible.
    extract_parameter_grid(
        input_file,
        optional_column_types=[
            FolderColumn,
            AccessionNumberColumn,
            PseudonymColumn,
            PseudonymColumn,
        ],
        required_column_types=[PseudonymColumn],
    )


def test_extract_parameter_grid_errors():
    """Tese a few situations that should raise errors"""

    input_file = ExcelFile(
        LOCAL_RESOURCE_PATH / "example_deid_form_missing_values.xlsx"
    )
    with pytest.raises(InputFileException):
        extract_parameter_grid(input_file)


def test_extract_paths():
    """Parse a list of paths"""

    input_file = ExcelFile(LOCAL_RESOURCE_PATH / "some_folder_names.xlsx")
    grid = extract_parameter_grid(input_file, optional_column_types=[FolderColumn])

    assert len(grid.rows) == 3  # this should be three rows
    assert len(grid.rows[0]) == 1  # should just have picked up path, not other column
    assert [str(row[0].path) for row in grid.rows] == [
        r"Kees\01",
        r"Henk\10",
        r"Kees\02",
    ]


def test_find_no_parameters():
    """When no column can be found, exceptions should be raised"""
    input_file = ExcelFile(
        LOCAL_RESOURCE_PATH / "example_deid_form_missing_values.xlsx"
    )

    with pytest.raises(InputFileException):
        # FolderColumn is not present in this file
        extract_parameter_grid(input_file, optional_column_types=[FolderColumn])


@pytest.mark.parametrize(
    "input_file_name",
    [
        "test_colon_sep.csv",
        "test_comma_sep.csv",
        "test_comma_sep.txt",
        "test_excel_2007-2013_XML.xlsx",
    ],
)
def test_reading_from_different_file_types(input_file_name):
    """Load the same data written to different file formats. Should all work"""
    input_file = as_tabular_file(FORMATS_PATH / input_file_name)
    grid = extract_parameter_grid(input_file)

    assert [str(x) for x in grid.rows[0]] == [
        "accession_number,1234567.12345678",
        "pseudo_name,patient1",
    ]
    assert [str(x) for x in grid.rows[1]] == [
        "accession_number,2234567.12345679",
        "pseudo_name,patient2",
    ]


def test_reading_single_column():
    """A single column should be valid, but contains no separators.
    This should not be a problem
    """
    input_file = as_tabular_file(LOCAL_RESOURCE_PATH / "test_single_line.csv")
    assert len(list(input_file.rows())) == 4  # there are 4 lines in this file

    grid = extract_parameter_grid(input_file)
    assert len(grid.rows) == 3
    assert str(grid.rows[2][0].path) == "andanother"
