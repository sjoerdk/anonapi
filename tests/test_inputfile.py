from anonapi.inputfile import read_file
from tests import RESOURCE_PATH


def test_read_simple_xls():
    """Parse parameters from a simple xls file with two rows and some comments
    at the top
    """
    input_file = RESOURCE_PATH / "test_inputfile" / "example_deid_form.xlsx"
    grid = read_file(input_file)
    assert [str(x) for x in grid.rows[0]] == [
        "accession_number,1234567.12345678",
        "patient_name,patient1",
    ]
    assert [str(x) for x in grid.rows[1]] == [
        "accession_number,2234567.12345679",
        "patient_name,patient2",
    ]
