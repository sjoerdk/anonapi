"""Custom click parameter types"""
import os
import re
from typing import List

import click
from click.types import ParamType
from pathlib import Path

from fileselection.fileselection import (
    FileSelectionFile,
    FileSelectionException,
)

from anonapi.context import AnonAPIContext
from anonapi.inputfile import (
    ALL_COLUMN_TYPES,
    AccessionNumberColumn,
    FolderColumn,
    InputFileError,
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
        """If it looks like 'int-int' try to turn into range. Otherwise, just
        leave as is and put in list

        Returns
        -------
        List[str]
            The value passed, or expanded range of ints represented by value passed

        """
        if value is None:
            return value

        if type(value) is list:
            return value  # Make sure function is idempotent. Feeding output
            # into convert() again will not change output

        match = re.match("^(?P<start>[0-9]+)-(?P<end>[0-9]+)$", value)
        if match:  # expand range and add each item
            return [
                str(x)
                for x in range(int(match["start"]), int(match["end"]) + 1)
            ]
        else:
            return [value]

    def __repr__(self):
        return "JOB_ID_RANGE"


class JobIDCollectionParamType(ParamType):
    """A comma-separated list of job ids and job id ranges

    For example:
    * 123 -> single job
    * 123-140 -> range
    * 123,125 -> multiple
    * 123,125,127-140 -> multiple + range
    """

    name = "job_id_collection"

    def convert(self, value, param, ctx) -> List[str]:
        """If it looks like 'int-int' try to turn into range. Otherwise, just
        leave as is and put in list

        Raises
        ------
        click.exceptions.BadParameter
            If a number range is ill formatted (non-int elements) or a range is
            reversed

        Returns
        -------
        List[str]
            A list of string values. For ranges, these are expanded, for non-ranges
            the value could be non-int. Sorting is all ints sorted by int value,
            followed by all non-int values sorted alphabetically
        """
        if value is None:
            return value

        if type(value) is list:
            return value  # Make sure function is idempotent. Feeding output
            # into convert() again will not change output

        all_jobs = set()
        for element in value.split(","):  # split on commas
            match = re.match("^(?P<start>[0-9]+)-(?P<end>[0-9]+)$", element)
            if match:  # expand range and add each item
                start = int(match["start"])
                end = int(match["end"])
                ids = [str(x) for x in range(start, end + 1)]
                if len(ids) == 0:
                    self.fail(
                        f"'{element}' looks like a number range, but cannot be "
                        f"expanded. Maybe a typo?"
                    )
                all_jobs.update(ids)
            elif "-" in element:
                self.fail(
                    f"'{element}' looks like a number range (with a '-'), but "
                    f"cannot be expanded. Maybe a typo?"
                )
            elif " " in element:
                self.fail(
                    f"'{element}' has a space in it, but this is not allowed. "
                    f"Looks too much like parameter separator."
                )
            else:
                all_jobs.add(element)  # this was a regular job id

        # sort ints and non-ints separately

        return self.sort_numbers_strings(all_jobs)

    @staticmethod
    def sort_numbers_strings(input_list: List[str]):
        """Sort a list of strings which might contain integer strings. Respect
        integers so that you won't get 10001 as lower than 2 (true for alphabetic
        sorting)
        """
        ints, non_ints = [], []
        for x in input_list:
            ints.append(int(x)) if x.isdigit() else non_ints.append(x)
        return [str(x) for x in sorted(ints)] + sorted(non_ints)

    def __repr__(self):
        return "JOB_ID_COLLECTION"


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
                f"'{value}' is not a registered anonymization server. "
                f"Options: {allowed}"
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
            with open(filepath) as f:
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
                paths = [
                    x for x in Path(os.getcwd()).glob(value) if x.is_dir()
                ]
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
        except InputFileError as e:
            self.fail(str(e), param, ctx)


class PathParameterFile(TabularParameterFile):
    name = "file containing paths"
    required_column_types = [FolderColumn]
    optional_column_types = [PseudonymColumn]


class AccessionNumberFile(TabularParameterFile):
    name = "file containing accession numbers"
    required_column_types = [AccessionNumberColumn]
    optional_column_types = [PseudonymColumn]
