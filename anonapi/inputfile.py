"""Classes and functions Reading job parameter_types from csv and excel files

These files contain tabular data with identifiers such as accession numbers
and optionally pseudonyms.
It is often easier to add such a file to a mapping then to alter-copy-paste between
files
"""
from typing import Iterator, List, Type, Union

from openpyxl.reader.excel import load_workbook

from anonapi.exceptions import AnonAPIException
from anonapi.mapper import JobParameterGrid
from anonapi.parameters import (
    AccessionNumber,
    Parameter,
    ParameterFactory,
    ParameterParsingError,
    PatientName,
)


class ParameterColumn:
    """A column of Parameter instances, like accession numbers or pseudonyms
    supposed to be part of a grid like a csv file or xls file

    Does fuzzy finding of column header and parsing of values
    """

    header_names: List[str] = []  # the column_types that could be above this column

    # the type of parameter that this column contains
    parameter_type: Type[Parameter] = Parameter

    def __init__(self, column: int):
        """

        Parameters
        ----------
        column: Optional[int]
            The 0-based column in which this header instance is found
        """
        self.column = column

    def __str__(self) -> str:
        if self.header_names:
            return f"Column {self.header_names[0]}"
        else:
            return "Column"

    @staticmethod
    def clean_string(string):
        """Make lowercase and remove separators"""
        return (
            string.replace(" ", "")
            .replace("_", "")
            .replace("-", "")
            .replace(".", "")
            .lower()
        )

    @classmethod
    def matches_header(cls, input: Union[str, None]) -> bool:
        """The given input seems to be this column's header"""
        if input is None:
            return False
        if cls.clean_string(input) in [cls.clean_string(x) for x in cls.header_names]:
            return True
        else:
            return False

    def parameter_from_row(self, row: List[str]) -> Parameter:
        """Try to parse a Parameter instance out of a row from the grid

        Raises
        ------
        InputFileParseException
            When this row cannot be parsed into the expected Parameter type
        """
        try:
            return ParameterFactory.parse_from_key_value(
                key=self.parameter_type.field_name,
                value=row[self.column],
                parameter_types=[self.parameter_type],
            )
        except ParameterParsingError as e:
            raise InputFileParseException(e)

    def has_empty_value(self, row: List[str]) -> bool:
        """True if the given row has no value in this column"""
        return row[self.column] == ""


class AccessionNumberColumn(ParameterColumn):

    header_names = ["Accession Number", "Acc Nr"]
    parameter_type: Type[Parameter] = AccessionNumber


class PseudonymColumn(ParameterColumn):

    header_names = ["PseudoID", "Pseudonym"]
    parameter_type: Type[Parameter] = PatientName


def parse_columns(
    row: List[str], column_types: List[Type[ParameterColumn]]
) -> List[ParameterColumn]:
    """Try to find known column types in row

    Parameters
    ----------
    row: List[str]
        The row of values to parse
    column_types: List[Type[ParameterColumn]]
        The types of columns to try
    """
    columns = []

    for idx, item in enumerate(row):
        for column_type in column_types:
            if column_type.matches_header(item):
                columns.append(column_type(column=idx))

    return columns


def find_column_headers(
    row_iterator: Iterator[List[str]], column_types: List[Type[ParameterColumn]]
) -> List[ParameterColumn]:
    """Go through each row in iterator until you find a row containing column headers

    Raises
    ------
    InputFileException
        When no column headers can be found
    column_types: List[Type[ParameterColumn]]
        The types of columns to look for
    """
    for row in row_iterator:
        columns = parse_columns(row, column_types=column_types)
        if columns:
            #  TODO: print where in files headers are found. Probably use logger
            return columns
    raise InputFileException("Could not find ")


def read_file(file_path: str) -> JobParameterGrid:
    """Read an xls file to extract parameter_types for jobs"""
    # read in xlsx reader

    column_types = [AccessionNumberColumn, PseudonymColumn]

    wb2 = load_workbook(file_path)
    sheet = wb2[wb2.sheetnames[0]]

    row_iterator = sheet.values
    columns = find_column_headers(row_iterator, column_types=column_types)

    # column headers found. Build a grid one row at a time
    grid = []
    for row in row_iterator:
        try:
            check_row(row, columns=columns)
        except EmptyRow:
            continue  # skip empty row, try next
        except PartiallyEmptyRow:
            # this is a problem. Raise further
            raise
        # checking was OK, parse
        try:
            grid.append([column.parameter_from_row(row) for column in columns])
        except ParameterParsingError as e:
            InputFileParseException(f"Error parsing row {row}: {e}")

    return JobParameterGrid(grid)


def check_row(row: List[str], columns: List[ParameterColumn]):
    """Is this row fit for parsing?

    Raises
    ------
    EmptyRow
        When row is empty
    PartiallyEmptyRow
        When some columns are filled but not all
    """
    filled = []
    empty = []
    for column in columns:
        if column.has_empty_value(row):
            empty.append(column)
        else:
            filled.append(column)

    if not filled:
        raise EmptyRow()
    if filled and empty:
        raise PartiallyEmptyRow(
            f"Problem in row {row}. Columns[{[str(x) for x in filled]}] have a value,"
            f" but columns [{[str(x) for x in empty]}] are empty. What do you want?"
        )


def columns_are_all_empty(row: List[str], columns: List[ParameterColumn]) -> bool:
    return all(column.has_empty_value(row) for column in columns)


def columns_are_partially_empty(row: List[str], columns: List[ParameterColumn]) -> bool:
    empty = [column.has_empty_value(row) for column in columns]
    return any(empty) and not all(empty)


class InputFileException(AnonAPIException):
    pass


class InputFileParseException(InputFileException):
    pass


class EmptyRow(AnonAPIException):
    pass


class PartiallyEmptyRow(AnonAPIException):
    pass
