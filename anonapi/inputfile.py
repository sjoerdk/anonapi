"""Classes and functions Reading job parameter_types from csv and excel files

These files contain tabular data with identifiers such as accession numbers
and optionally pseudonyms.
It is often easier to add such a file to a mapping then to alter-copy-paste between
files
"""
from typing import Iterator, List, Type, Union, Optional

from openpyxl.reader.excel import load_workbook

from anonapi.exceptions import AnonAPIException
from anonapi.mapper import JobParameterGrid
from anonapi.parameters import (
    AccessionNumber,
    Parameter,
    ParameterFactory,
    ParameterParsingError,
    PathParameter,
    PseudoName,
)


class ParameterColumn:
    """A column of Parameter instances, like accession numbers or pseudonyms
    supposed to be part of a grid like a csv file or xls file

    Does fuzzy finding of column header and parsing of values
    """

    header_names: List[str] = []  # the column_types that could be above this column

    # the type of parameter that this column contains
    parameter_type: Type[Parameter] = Parameter

    def __init__(self, column: int, header_row_idx: int = 0):
        """

        Parameters
        ----------
        column: int
            The 0-based column in which this header instance is found
        header_row_idx: int, optional
            The 0-based row where this column's header is found. For better
            error messages (print row in file where an error occurred)
        """
        self.column = column
        self.header_row_idx = header_row_idx

    def __str__(self) -> str:
        if self.header_names:
            return f"Column {self.header_names[0]}"
        else:
            return "Column"

    @staticmethod
    def clean_string(string: str):
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

    @classmethod
    def header_name(cls) -> str:
        """A header name that his header might have. For helpful error messages"""
        if cls.header_names:
            return cls.header_names[0]
        else:
            return ""

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

        return row[self.column] == "" or row[self.column] is None


class AccessionNumberColumn(ParameterColumn):

    header_names = ["Accession Number", "Acc Nr"]
    parameter_type: Type[Parameter] = AccessionNumber


class PseudonymColumn(ParameterColumn):

    header_names = ["PseudoID", "Pseudonym"]
    parameter_type: Type[Parameter] = PseudoName


class FolderColumn(ParameterColumn):

    header_names = ["folder", "map", "path"]
    parameter_type: Type[Parameter] = PathParameter


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

    Parameters
    ----------
    row_iterator: Iterator[List[str]]
        iterator returning lists of strings corresponding to each row of a
        grid-like file
    column_types: List[Type[ParameterColumn]]
        The types of columns to look for

    Returns
    -------
    List[ParameterColumn]
        All parameter columns found

    Raises
    ------
    InputFileException
        When no column headers can be found

    """

    for idx, row in enumerate(row_iterator):
        columns = parse_columns(row, column_types=column_types)
        if columns:
            # add column header row idx for better error messages later
            for column in columns:
                column.header_row_idx = idx
            return columns
    raise InputFileException(
        f"Could not find any column headers. Looked for any"
        f" of [{','.join([x.header_name() for x in column_types])}]"
    )


def cast_rows_to_string(iterator: Iterator[List]) -> Iterator[List[Optional[str]]]:
    """For standardizing data from grid-like files. Make everything string,
    except None values. Keep those None.

    """

    def str_preserve_none(input):
        if input is None:
            return None
        else:
            return str(input)

    for row in iterator:
        yield list(map(str_preserve_none, row))


def extract_parameter_grid(
    file_path: str, column_types: List[Type[ParameterColumn]] = None
) -> JobParameterGrid:
    """Read an xls file and try to extract a grid of parameters

    Parameters
    ----------
    file_path: str
        Extract from this file
    column_types: List[Type[ParameterColumn]], optional
        Search for these column types. Defaults to AccessionNumber and Pseudonym


    Raises
    ------
    InputFileException
        If parsing or reading fails for any reason

    """
    # read in xlsx reader
    if column_types is None:
        column_types = [AccessionNumberColumn, PseudonymColumn]

    wb2 = load_workbook(file_path)
    sheet = wb2[wb2.sheetnames[0]]

    row_iterator = cast_rows_to_string(sheet.values)

    columns = find_column_headers(row_iterator, column_types=column_types)

    column_headers_idx = columns[0].header_row_idx

    # column headers found. Build a grid one row at a time
    grid = []
    for idx, row in enumerate(row_iterator):
        try:
            grid.append(parse_row(row, columns=columns))
        except EmptyRow:
            continue  # skip empty row, try next
        except RowParseException as e:
            # Add row number (+2 as excel rows start at 1 and both idxs are 0-based)
            raise InputFileParseException(
                f"Exception in row {column_headers_idx+idx+2}: {e}"
            )

    return JobParameterGrid(grid)


def parse_row(row: List[str], columns: List[ParameterColumn]) -> List[Parameter]:
    """Is this row fit for parsing? Are there missing parameters? empty values?

    Parameters
    ----------
    row: List[str]
        String value of each cell in this row
    columns: List[ParameterColumn])
        The column names for each value in row

    Returns
    -------
    List[Parameter]
        Each value in row parsed according to column type

    Raises
    ------
    EmptyRow
        When row is empty
    PartiallyEmptyRow
        When some columns are filled but not all
    InputFileParseException
        When any of the values in row cannot be parsed according to their columns
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
        raise RowParseException(
            f"Problem in row {row}. Columns[{[str(x) for x in filled]}] have a value,"
            f" but columns [{[str(x) for x in empty]}] are empty. What do you want?"
        )
    return [column.parameter_from_row(row) for column in columns]


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


class RowParseException(AnonAPIException):
    pass
