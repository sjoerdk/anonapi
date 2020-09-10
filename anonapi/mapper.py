"""Makes it possible to map source files to anonymized id, name etc.
Pre-processing step for creating IDIS jobs

Meant to be usable in a command line, with minimal windows editing tools. Maybe
Excel, maybe notepad

"""
import csv
import os
from csv import Dialect
from typing import List, Optional, TextIO, Union

from tabulate import tabulate

from anonapi.exceptions import AnonAPIException
from anonapi.parameters import (
    FolderIdentifier,
    FileSelectionIdentifier,
    Parameter,
    StudyInstanceUIDIdentifier,
    AccessionNumberIdentifier,
    SourceIdentifierParameter,
    ParameterFactory,
    PatientName,
    PatientID,
    Description,
    ALL_PARAMETERS,
    ParameterParsingError,
)
from collections import defaultdict
from io import StringIO
from pathlib import Path
from os import path


class Mapping:
    """Everything needed for creating anonymization jobs

    Wrapper around JobParameterGrid that adds description and mapping-wide settings
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
            Defaults to empty string
        dialect: Union[str, Dialect], optional
            CSV dialect. Which line separator to use etc. Any Dialect or a string
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

    def save(self, f):
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
    def load(cls, f):
        """Load a mapping from a csv file stream"""
        # split content into three sections

        try:
            sections = cls.parse_sections(f)
        except OSError as e:
            if "raw readinto() returned invalid length" in str(e):
                raise MappingLoadError(
                    f"Cannot load mapping. Is the mapping file opened in any"
                    f" editor?. Original error: {e}"
                )
            else:
                # Unsure which error this is. Can't handle this here.
                raise

        description = "".join(sections[cls.DESCRIPTION_HEADER])

        options = [
            ParameterFactory.parse_from_string(line)
            for line in sections[cls.OPTIONS_HEADER]
        ]

        grid_content = StringIO(os.linesep.join(sections[cls.GRID_HEADER]))
        dialect = sniff_dialect(grid_content)
        grid = JobParameterGrid.load(grid_content)
        return cls(grid=grid, options=options, description=description, dialect=dialect)

    @classmethod
    def parse_sections(cls, f):
        """A mapping csv file consists of three sections divided by headers.
         Try to parse each one. Also cleans each line

        Parameters
        ----------
        f: file handled opened with read flag

        Returns
        -------
        Dict
            A dict with all lines under each of the headers in cls.ALL_HEADERS
            Line endings and trailing commas have been stripped. empty lines
            have been removed

        Raises
        ------
        MappingLoadError
            If not all headers can be found or are not in the expected order

        """
        collected = defaultdict(list)
        headers_to_find = cls.ALL_HEADERS.copy()
        header_to_find = headers_to_find.pop(0)
        current_header = None
        for line in f.readlines():
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

        # check the results do we have all headers?
        if headers_to_find:
            raise MappingLoadError(
                f'Could not find required headers "{headers_to_find}"'
            )

        return collected

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

    def add_row(self, parameters):
        """Add the given parameters in a new row in this mapping

        Parameters
        ----------
        parameters: List[Parameter]
            The parameters to create one job

        """
        self.grid.rows.append(parameters)

    def to_string(self):
        """Human readable multi-line description of this mapping

        Returns
        -------
        str
        """
        output = self.description
        output += "\n" + self.grid.to_table_string()
        return output


def sniff_dialect(f: TextIO, max_lines: int = 3) -> Dialect:
    """Try to find out the separator character etc. from given opened csv file

    Parameters
    ----------
    f: TextIO
        Open file handle to csv file
    max_lines: int, optional
        sniff this many lines. If dialect is still not found then,
        Raise exception. Defaults to 3

    Raises
    ------
    AnonAPIException:
        When dialect cannot be determined

    """
    tried = 0
    for line in f:
        tried += 1
        try:
            dialect = csv.Sniffer().sniff(line, delimiters=";,")
            f.seek(0)
            return dialect
        except csv.Error as e:
            if tried < max_lines:
                continue
            else:
                raise AnonAPIException(e)

    raise AnonAPIException("Could not determine dialect for csv file")


class JobParameterGrid:
    """A persistable 2D grid of job rows. Each row belongs to one job"""

    def __init__(self, rows):
        """

        Parameters
        ----------
        rows: List[List[Parameter]]
        """

        self.rows = rows

    def __len__(self):
        return len(self.rows)

    def save(self, f: TextIO, dialect: Union[str, Dialect] = "excel"):
        """Write rows as CSV. Will omit columns where each value is none

        Parameters
        ----------
        f: TextIO
            Write to this
        dialect: Union[str, Dialect], optional
            CSV dialect. Which line separator to use etc. Any Dialect or a string
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
        dialect = sniff_dialect(f)
        reader = csv.DictReader(f, dialect=dialect)
        parameters = []
        try:
            for row in reader:
                parameters.append(
                    [
                        ParameterFactory.parse_from_key_value(key, val)
                        for key, val in row.items()
                    ]
                )

        except ParameterParsingError as e:
            raise MappingLoadError(f"Problem parsing '{row}': {e}")

        return cls(parameters)

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

    def to_table_string(self):
        """A source - patient_id command_table with a small header

        Returns
        -------
        str:
            Nice string representation of this list, 80 chars wide, truncated if
            needed

        """
        # remember parameter list can be sparse
        table = defaultdict(list)
        types = [SourceIdentifierParameter, PatientID]

        for row in self.rows:
            typed_row = {type(x): x for x in row}
            for param_type in types:
                try:
                    instance = typed_row[param_type]
                except KeyError:
                    instance = param_type()
                table[param_type.field_name].append(instance.value)
        output = f"Parameter grid with {len(self.rows)} rows:\n\n"
        output += tabulate(table, headers="keys", tablefmt="simple")
        return output


class MappingFolder:
    """Folder that might contain a mapping.

    Uses a single default filename that it expects mapping to be saved under.

    """

    DEFAULT_FILENAME = "anon_mapping.csv"

    def __init__(self, folder_path):
        """

        Parameters
        ----------
        root_path: Pathlike
            root_path to this folder
        """
        self.folder_path = Path(folder_path)

    def full_path(self):
        return self.folder_path / self.DEFAULT_FILENAME

    def make_relative(self, path):
        """Make the given root_path relative to this mapping folder

        Parameters
        ----------
        path: Pathlike

        Returns
        -------
        Path
            Path relative to this mapping folder

        Raises
        ------
        MapperException
            When root_path cannot be made relative

        """
        path = Path(path)
        if not path.is_absolute():
            return path
        try:
            return path.relative_to(self.folder_path)
        except ValueError as e:
            raise MapperException(f"Error making root_path relative: {e}")

    def make_absolute(self, path):
        """Get absolute root_path to the given root_path, assuming it is in this mapping folder

        Parameters
        ----------
        path: Pathlike

        Returns
        -------
        Path
            Absolute root_path, assuming mapping folder as base folder

        Raises
        ------
        MapperException
            When given root_path is already absolute

        """
        path = Path(path)
        if path.is_absolute():
            raise MapperException("Cannot make absolute root_path absolute")
        return self.folder_path / Path(path)

    def has_mapping(self):
        """Is there a mapping file in this folder?"""
        return self.full_path().exists()

    def save_mapping(self, mapping: Mapping):
        with open(self.full_path(), "w", newline="") as f:
            mapping.save(f)

    def load_mapping(self):
        """Load Mapping from default location in this folder

        Returns
        -------
        Mapping

        """
        with open(self.full_path(), "r", newline="") as f:
            return Mapping.load(f)

    def delete_mapping(self):
        os.remove(self.full_path())

    def get_mapping(self):
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
            with open(self.full_path(), "r", newline="") as f:
                return Mapping.load(f)
        except FileNotFoundError:
            raise NoMappingFoundError("No mapping defined in current directory")
        except MapperException as e:
            raise MappingLoadError(e)


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
                PatientName("Patient1"),
                PatientID("001"),
                Description("All files from folder1"),
            ],
            [
                SourceIdentifierParameter(
                    StudyInstanceUIDIdentifier("123.12121212.12345678")
                ),
                PatientName("Patient2"),
                PatientID("002"),
                Description(
                    "A study which should be retrieved from PACS, "
                    "identified by StudyInstanceUID"
                ),
            ],
            [
                SourceIdentifierParameter(
                    AccessionNumberIdentifier("12345678.1234567")
                ),
                PatientName("Patient3"),
                PatientID("003"),
                Description(
                    "A study which should be retrieved from PACS, "
                    "identified by AccessionNumber"
                ),
            ],
            [
                SourceIdentifierParameter(
                    FileSelectionIdentifier(Path("folder2/fileselection.txt"))
                ),
                PatientName("Patient4"),
                PatientID("004"),
                Description("A selection of files in folder2"),
            ],
        ]

        super().__init__(rows=rows)


class MapperException(AnonAPIException):
    pass


class NoMappingFoundError(MapperException):
    pass


class MappingLoadError(MapperException):
    pass
