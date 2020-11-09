"""Custom click parameter types"""
import os
import re
from typing import List

import click
from click.types import ParamType
from pathlib import Path

from fileselection.fileselection import FileSelectionFile, FileSelectionException

from anonapi.context import AnonAPIContext
from anonapi.inputfile import (
    ALL_COLUMN_TYPES,
    AccessionNumberColumn,
    FolderColumn,
    InputFileException,
    PseudonymColumn,
    as_tabular_file,
    extract_parameter_grid,
)


class JobIDRangeParamType(ParamType):
    """A parameter that is either a single job ID "8" or a range of job ids "5-15".
    Will expand any range into a tuple min until max. Min and max inclusive

    """

    name = "job_id"

    def convert(self, value, param, ctx) -> List[str]:
        """If it looks like 'int-int' try to turn into range. Otherwise just leave as is and put in list

        Returns
        -------
        List[str]
            The value passed, or expanded range of ints represented by value passed

        """
        if value is None:
            return value

        if type(value) is list:
            return value  # Make sure function is idempotent. Feeding output into convert() again will not change output

        match = re.match("^(?P<start>[0-9]+)-(?P<end>[0-9]+)$", value)
        if match:  # expand range and add each item
            return [str(x) for x in range(int(match["start"]), int(match["end"]) + 1)]
        else:
            return [value]

    def __repr__(self):
        return "JOB_ID_RANGE"


class AnonServerKeyParamType(ParamType):
    """A key to a registered anonapi server. Yields nice message when not found"""

    name = "anon_server_key"

    def convert(self, value, param, ctx):
        if not ctx:
            self.fail("This type expects an AnonAPIContext object in context")
        context: AnonAPIContext = ctx.obj

        allowed = [x.name for x in context.settings.servers]
        if value not in allowed:
            self.fail(
                f"'{value}' is not a registered anonymization server. Options: {allowed}"
            )
        return value

    def __repr__(self):
        return "ANON_SERVER_KEY"


class FileSelectionFileParam(ParamType):
    """A path to a file that can parsed as FileSelection"""

    name = "file_selection_file"

    def convert(self, value, param, ctx):
        filepath = Path(value)
        if not filepath.exists():
            self.fail(f"No file selection found at '{filepath}'")
        try:
            with open(filepath, "r") as f:
                return FileSelectionFile.load(f, datafile=filepath)
        except FileSelectionException as e:
            self.fail(f"Error reading file selection: {e}")

    def __repr__(self):
        return "FILE_SELECTION_FILE"


class WildcardFolder(ParamType):
    """A folder path that might contain asterisks * as wildcard

    After expanding any wildcards, converts to Path with click.Path()
    """

    name = "wildcard_folder"

    def __init__(self, exists=False):
        """

        Parameters
        ----------
        exists: Bool, optional
            If True, will check each folder before returning it
        """
        self.exists = exists

    def convert(self, value, param, ctx) -> List[Path]:
        if not value:
            return None
        else:
            # convert to Path using click's own Path parameter
            convert = click.Path(exists=self.exists).convert
            if "*" in value:
                paths = [x for x in Path(os.getcwd()).glob(value) if x.is_dir()]
                return [convert(x, param, ctx) for x in paths]
            else:
                return [convert(value, param, ctx)]


class TabularParameterFile(ParamType):
    """A file path to a file containing parameters in a tabular format

    Will parse file and return the parsed results
    """

    name = "tabular parameter file"
    required_column_types = []  # fail if not found
    optional_column_types = ALL_COLUMN_TYPES

    def convert(self, value, param, ctx):
        if value is None:
            return None  # required by click
        try:
            return extract_parameter_grid(
                file=as_tabular_file(value),
                optional_column_types=self.optional_column_types,
                required_column_types=self.required_column_types,
            )
        except InputFileException as e:
            self.fail(str(e), param, ctx)


class PathParameterFile(TabularParameterFile):
    name = "file containing paths"
    required_column_types = [FolderColumn]
    optional_column_types = [PseudonymColumn]


class AccessionNumberFile(TabularParameterFile):
    name = "file containing accession numbers"
    required_column_types = [AccessionNumberColumn]
    optional_column_types = [PseudonymColumn]
