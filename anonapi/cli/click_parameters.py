"""Custom parameters for click command line"""
import os
from pathlib import Path
from typing import List

import click


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
