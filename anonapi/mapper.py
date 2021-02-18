"""Makes it possible to map a structured file to batch of IDIS jobs.
The file should contain source files to anonymized id, name etc.
Pre-processing step for creating IDIS jobs

Notes
-----
The main class `Mapping` contains a human readable description, some general
options, and a JobParameterGrid which contains one row per job, one parameter
per column.
Originally, The bare JobParameterGrid was named `Mapping`. Later on this turned out
to be insufficient as more information needed to be saved. Some confusing naming might
still exist in some places in the code, referring to JobParameterGrid objects as
mappings. This should be renamed whenever encountered
"""
import csv
import locale
import logging
import os

from csv import Dialect
from typing import Dict, Iterable, List, Optional, TextIO, Union

from tabulate import tabulate

from anonapi.exceptions import AnonAPIException
from anonapi.parameters import (
    FolderIdentifier,
    FileSelectionIdentifier,
    Parameter,
    ParameterException,
    ParameterSet,
    StudyInstanceUIDIdentifier,
    AccessionNumberIdentifier,
    SourceIdentifierParameter,
    ParameterFactory,
    PseudoName,
    Description,
    ALL_PARAMETERS,
    ParameterParsingError,
)
from collections import defaultdict
from io import StringIO
from pathlib import Path
from os import path

DEFAULT_MAPPING_NAME = "anon_mapping.csv"  # Filename for mapping if not specified

logger = logging.getLogger(__name__)


class Mapping:
    """All information needed for creating anonymization jobs

    Contains a JobParameterGrid plus description and mapping-wide settings
    such as output dir
    """

    # Headers used in between sections in csv file
    DESCRIPTION_HEADER = "## Description ##"
    OPTIONS_HEADER = "## Options ##"
    GRID_HEADER = "## Mapping ##"
    ALL_HEADERS = [DESCRIPTION_HEADER, OPTIONS_HEADER, GRID_HEADER]

    def __init__(
        self,
        grid: "JobParameterGrid",
        options: Optional[List[Parameter]] = None,
        description="",
        dialect: Union[str, Dialect] = "excel",
    ):
        """

        Parameters
        ----------
        grid: JobParameterGrid
            The per-job command_table of parameters
        options: List[Parameter], optional
            List of rows that have been set for the entire mapping. Defaults to empty
        description: str, optional
            Human readable description of this mapping. Can contain newline chars.
            Defaults to empty input
        dialect: Union[str, Dialect], optional
            CSV dialect. Which line separator to use etc. Any Dialect or a input
            returned by the list_dialects() function.
            Defaults to 'excel'
        """
        self.grid = grid
        if options is None:
            options = []
        self.options = options
        self.description = description
        if type(dialect) == str:
            self.dialect = csv.get_dialect(dialect)
        else:
            self.dialect = dialect

    def __len__(self):
        return len(self.grid)

    def save_to(self, f: TextIO):
        """Write this Mapping to given stream"""
        # write description
        f.write(self.DESCRIPTION_HEADER + self.dialect.lineterminator)
        f.write(self.description)
        f.write(self.dialect.lineterminator)

        # write options
        f.write(self.OPTIONS_HEADER + self.dialect.lineterminator)
        f.write(
            self.dialect.lineterminator.join(
                [x.to_string(delimiter=self.dialect.delimiter) for x in self.options]
            )
        )
        f.write(self.dialect.lineterminator)
        f.write(self.dialect.lineterminator)

        # write mapping
        f.write(self.GRID_HEADER + self.dialect.lineterminator)
        mapping_content = StringIO()
        self.grid.save(mapping_content, dialect=self.dialect)
        mapping_content.seek(0)
        f.write(mapping_content.read())

    @classmethod
    def load(cls, lines: Iterable[str]):
        """Load a mapping from lines

        Parameters
        ----------
        lines: Iterable[str]
            Load object from these lines
        """

        try:
            lines = [x for x in lines]  # make sure open file handles are read through
        except OSError as e:
            if "raw readinto() returned invalid length" in str(e):
                raise MappingLoadError(
                    f"Cannot load mapping. Is the mapping file opened in any"
                    f" editor?. Original error: {e}"
                )
            else:
                # Unsure which error this is. Can't handle this here.
                raise

        # split content into three sections
        sections = cls.parse_sections(lines)
        description = "".join(sections[cls.DESCRIPTION_HEADER])

        options = [
            ParameterFactory.parse_from_string(line)
            for line in sections[cls.OPTIONS_HEADER]
            if parameter_line_is_empty(line)
        ]

        grid_content = os.linesep.join(sections[cls.GRID_HEADER])
        grid = JobParameterGrid.load(StringIO(grid_content))
        return cls(
            grid=grid,
            options=options,
            description=description,
            dialect=sniff_dialect_safe(lines),
        )

    @classmethod
    def parse_sections(cls, lines: Iterable[str]):
        """A mapping csv file consists of three sections divided by column_types.
         Try to parse each one. Also cleans each line

        Parameters
        ----------
        lines: Iterable[str]
            lines to parse

        Returns
        -------
        Dict
            A dict with all lines under each of the column_types in cls.ALL_HEADERS
            Line endings and trailing commas have been stripped. empty lines
            have been removed

        Raises
        ------
        MappingLoadError
            If not all column_types can be found or are not in the expected order

        """
        collected = defaultdict(list)
        headers_to_find = cls.ALL_HEADERS.copy()
        header_to_find = headers_to_find.pop(0)
        current_header = None
        for line in lines:
            line = line.replace("\r", "").replace("\n", "").rstrip(",").rstrip(";")
            if not line:  # skip empty lines
                continue
            if header_to_find.lower() in line.lower():
                # this is our header, start recording
                current_header = header_to_find
                # and look for the next one. If there is one.
                if headers_to_find:
                    header_to_find = headers_to_find.pop(0)
                continue  # skip header line itself
            if current_header:
                collected[current_header].append(line)

        # check the results do we have all column_types?
        if headers_to_find:
            raise MappingLoadError(
                f'Could not find required column_types "{headers_to_find}"'
            )

        return collected

    @property
    def rows(self):
        """All parameters for each row. This includes the parameters in the
        grid as well as the mapping-wide parameters in the options section.

        Grid parameters overrule mapping-wide parameters

        Returns
        -------
            List[Parameter] for each row in grid
        """
        rows = []
        for grid_row in self.grid.rows:
            row_dict = {type(x): x for x in self.options}
            row_dict.update({type(x): x for x in grid_row})
            rows.append(list(row_dict.values()))
        return rows

    def add_row(self, parameters: List[Parameter]):
        """Add the given list of parameters to this mapping as a new grid row

        Parameters
        ----------
        parameters: List[Parameter]
            The parameters to create one job

        """
        self.grid.append_row(parameters)

    def add_grid(self, grid: "JobParameterGrid"):
        """Add each row in given grid to this mapping"""
        self.grid.append_parameter_grid(grid)

    def to_string(self):
        """Human readable multi-line description of this mapping

        Returns
        -------
        str
        """
        output = self.description
        output += "\n" + self.grid.to_table_string(max_rows=5)
        return output


def sniff_dialect(lines: Iterable[str]) -> Dialect:
    """Try to find out the separator character etc. from given opened csv file

    Parameters
    ----------
    lines: Iterable[str]
        Lines to sniff

    Raises
    ------
    MapperException:
        When dialect cannot be determined

    """

    for line in lines:
        try:
            return csv.Sniffer().sniff(line, delimiters=";,")
        except csv.Error:
            continue  # just try all lines
    raise MapperException("Could not determine dialect for csv file")


def parameter_line_is_empty(line_in: str) -> bool:
    """True if the input line contains only separators or spaces. For cleaning"""
    return bool(line_in.replace(" ", "").replace(",", "").replace(";", ""))


def sniff_dialect_safe(
    lines: Iterable[str], default: Optional[str] = "excel"
) -> Dialect:
    """Try to find out the separator character etc. from given opened csv file.
    Return default if not found

    Parameters
    ----------
    lines: Iterable[str]
        lines to sniff
    default: Optional[str]
        return this dialect when dialect cannot be determined. Defaults to 'excel'
    """
    try:
        return sniff_dialect(lines)
    except MapperException as e:  # this could be a single-column mapping
        logger.debug(
            f"could not determine dialect, guessing "
            f"'{default}'. Original error: '{e}'"
        )
        return default


class JobParameterGrid:
    """A persistable 2D grid of job rows. Each row belongs to one job"""

    def __init__(self, rows: List[List[Parameter]]):

        self.rows = rows

    def __len__(self):
        return len(self.rows)

    def width(self) -> int:
        """Maximum number of columns in this grid"""
        return max([len(x) for x in self.rows])

    def append_row(self, row: List[Parameter]):
        """Append the given row to this grid"""
        self.rows.append(row)

    def append_parameter_grid(self, grid: "JobParameterGrid"):
        """Append all rows in the given grid"""
        for row in grid.rows:
            self.append_row(row)

    def save(self, f: TextIO, dialect: Union[str, Dialect] = "excel"):
        """Write rows as CSV. Will omit columns where each value is none

        Parameters
        ----------
        f: TextIO
            Write to this
        dialect: Union[str, Dialect], optional
            CSV dialect. Which line separator to use etc. Any Dialect or a input
            returned by the list_dialects() function.
            Defaults to 'excel'

        """
        if type(dialect) == str:  # cast to Dialect instance if needed
            dialect = csv.get_dialect(dialect)

        # Which parameter types are there?
        params = self.parameter_types()

        writer = csv.DictWriter(
            f, dialect=dialect, fieldnames=[x.field_name for x in params],
        )
        writer.writeheader()
        for row in self.rows:
            writer.writerow({x.field_name: x.value for x in row})

    @classmethod
    def load(cls, f):
        """Load an instance from open file handle

        Parameters
        ----------
        f
            file object opened for reading

        Returns
        -------
        JobParameterGrid
            Loaded from data in f

        Raises
        ------
        MappingLoadError:
            If mapping could not be loaded

        """
        lines = f.readlines()
        dialect = sniff_dialect_safe(lines)
        reader = csv.DictReader(lines, dialect=dialect)
        parameters = []
        try:
            for row in reader:
                parameters.append(JobParameterGrid.parse_job_parameter_row(row))
        except ParameterParsingError as e:
            raise MappingLoadError(f"Problem parsing '{row}': {e}")

        return cls(parameters)

    @staticmethod
    def parse_job_parameter_row(row: Dict[str, str]) -> List[Parameter]:
        """Parse a dict of strings as Parameters, perform some initial checks for
        more informative error messages

        Parameters
        ----------
        Dict[str, str]
            dict with parameter key: parameter value. As output by csv.DictReader

        Returns
        -------
        List[Parameter]

        Raises
        ------
        ParameterParsingError
        """
        # check common problem: missing column header
        keys = [x for x in row.keys() if x]  # remove None and empty
        values = list(row.values())
        if len(keys) < len(values):
            raise ParameterParsingError(
                f"Missing column header. I've got {len(values)} "
                f"values: {values} but only {len(keys)} headers: "
                f"({keys}). I don't know which is which now."
            )

        return [
            ParameterFactory.parse_from_key_value(key, val) for key, val in row.items()
        ]

    def parameter_types(self):
        """Sorted list of all classes of Parameter found in this list

        Useful if you want to make a nice command_table for example

        Returns
        -------
        List[class]
            Each distinct class of Parameter, ordered in the same order as
            rows.ALL_PARAMETERS

        """
        types = {type(param) for row in self.rows for param in row}
        return [x for x in ALL_PARAMETERS if x in types]

    def to_table_string(self, max_rows: Optional[int] = None):
        """A source - patient_id command_table with a small header

        Returns
        -------
        str:
            Nice input representation of this list, 80 chars wide, truncated if
            needed
        max_rows: Optional[int]
            If given, show at most this many rows of content. If not given,
            prints all

        """
        # remember parameter list can be sparse
        table = defaultdict(list)
        types = [SourceIdentifierParameter, PseudoName]

        if max_rows is None:
            rows = self.rows
        else:
            rows = self.rows[:max_rows]

        for row in rows:
            typed_row = {type(x): x for x in row}
            for param_type in types:
                try:
                    instance = typed_row[param_type]
                except KeyError:
                    instance = param_type()
                table[param_type.field_name].append(instance.value)

        if max_rows is None:
            output = f"Parameter grid with {len(self.rows)} rows:\n\n"
        else:
            output = (
                f"Parameter grid with {len(self.rows)} rows (showing at most "
                f"{max_rows}):\n\n"
            )
        output += tabulate(table, headers="keys", tablefmt="simple")
        return output


class MappingFile:
    """A file that contains a mapping"""

    def __init__(self, file_path: Path):
        self.file_path = file_path

    def save_mapping(self, mapping: Mapping):
        with open(self.file_path, "w", newline="") as f:
            mapping.save_to(f)

    def load_mapping(self) -> Mapping:
        """Load Mapping from default location in this folder

        Returns
        -------
        Mapping

        Raises
        ------
        MappingLoadError
            If mapping cannot be loaded

        """
        with open(self.file_path, "r", newline="") as f:
            try:
                return Mapping.load(f)
            except FileNotFoundError as e:
                raise MappingLoadError(f"Could not load mapping: {e}")

    def get_mapping(self) -> Mapping:
        """Load default mapping from this folder

        Returns
        -------
        Mapping
            Loaded from current dir

        Raises
        ------
        MapperException
            When no mapping could be loaded from current directory

        """
        try:
            with open(self.file_path, "r", newline="") as f:
                return Mapping.load(f)
        except (FileNotFoundError, MapperException) as e:
            raise MapperException(
                f"Could not load mapping at " f"'{self.file_path}': {e}"
            )


class ExampleJobParameterGrid(JobParameterGrid):
    """A mapping list with some example content. Gives an overview of possible
    identifiers
    """

    def __init__(self):
        rows = [
            [
                SourceIdentifierParameter(
                    FolderIdentifier(identifier=path.sep.join(["example", "folder1"]))
                ),
                PseudoName("Patient1"),
                Description("All files from folder1"),
            ],
            [
                SourceIdentifierParameter(
                    StudyInstanceUIDIdentifier("123.12121212.12345678")
                ),
                PseudoName("Patient2"),
                Description(
                    "A study which should be retrieved from PACS, "
                    "identified by StudyInstanceUID"
                ),
            ],
            [
                SourceIdentifierParameter(
                    AccessionNumberIdentifier("12345678.1234567")
                ),
                PseudoName("Patient3"),
                Description(
                    "A study which should be retrieved from PACS, "
                    "identified by AccessionNumber"
                ),
            ],
            [
                SourceIdentifierParameter(
                    FileSelectionIdentifier(Path("folder2/fileselection.txt"))
                ),
                PseudoName("Patient4"),
                Description("A selection of files in folder2"),
            ],
        ]

        super().__init__(rows=rows)


class MappingParameterSet(ParameterSet):
    """A set of parameters forming one row in a mapping. Defines defaults and
    restrictions
    """

    def __init__(self, parameters: List[Parameter]):
        """Create a parameter set to put in a mapping. Missing input parameters will
        be added with default values

        Parameters
        ----------
        parameters: List[Parameter]
            The parameters in this set

        Raises
        ------
        MapperException
            If mapping does not contain a source parameter. Without a source this
            is not valid to put in a mapping.

        """
        super().__init__(parameters=self.get_default_parameters())
        self.update(parameters)
        try:
            self.get_source_parameter()
        except ParameterException as e:
            raise MapperException(
                f"Invalid set of parameters for mapping: no source found. Where"
                f" should the data come from? Original error: {e}"
            )

    @staticmethod
    def get_default_parameters() -> ParameterSet:
        """Generate some reasonable defaults for pseudo name and description"""
        return ParameterSet(
            parameters=[
                ParameterFactory.generate_pseudo_name(),
                ParameterFactory.generate_description(),
            ]
        )


def get_local_dialect() -> Dialect:
    """Try to obtain best match for local CSV dialect

    Uses the heuristic that decimal separator comma goes together with
    list separator colon
    """
    if locale.localeconv()["decimal_point"] == ",":
        return ColonDelimited()
    else:
        return csv.excel


class MapperException(AnonAPIException):
    pass


class MappingLoadError(MapperException):
    pass


class ColonDelimited(csv.excel):
    """Excel csv dialect, but with colon ';' delimiter"""

    delimiter = ";"
