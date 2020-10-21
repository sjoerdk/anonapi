"""Custom parameters for click command line"""
import os
from pathlib import Path
from typing import List

import click

from anonapi import inputfile
from anonapi.inputfile import (
    AccessionNumberColumn,
    FolderColumn,
    InputFileException,
    PseudonymColumn,
    as_tabular_file,
    extract_parameter_grid,
)


class WildcardFolder(click.ParamType):
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


class TabularParameterFile(click.ParamType):
    """A file containing parameters in a tabular format"""

    name = "tabular parameter file"
    required_column_types = []  # fail if not found
    optional_column_types = inputfile.ALL_COLUMN_TYPES

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
