"""Functions to filter and select files from folders.
Useful for example for selecting only DICOM files in a folder.
"""
from fnmatch import fnmatch
from pathlib import Path
from time import sleep

import pydicom
from pydicom.errors import InvalidDicomError


class FileFolder:
    """A folder that might contain some files. Makes it easy to iterate
    over these files in different ways
    """

    def __init__(self, path):
        self.path = Path(path)

    def iterate(
        self, pattern="*", recurse=True, exclude_patterns=None, ignore_dotfiles=True
    ):
        """Iterator that yields subpaths. Makes it easy to use progress bar

        Parameters
        ----------
        pattern: str, optional
            Glob file pattern. Default is '*' (match all)
        recurse: bool, optional
            Search for paths in all underlying directories. Default is True
        exclude_patterns: List[str], optional
            Exclude any path that matches any of these patterns.
            Patterns are unix-style: * as wildcard. See fnmatch function.
            Defaults to emtpy list meaning no exclusions
        ignore_dotfiles: bool, optional
            Ignore any filename starting with '.'

        Returns
        -------
        generator
            Yields Path if the path is a file, None otherwise

        """
        if not exclude_patterns:
            exclude_patterns = []

        if recurse:
            glob_pattern = f"**/{pattern}"
        else:
            glob_pattern = f"{pattern}"

        all_paths_iter = self.path.glob(glob_pattern)
        for x in all_paths_iter:
            # sleep(0.2)
            exclude = any(
                [fnmatch(x.relative_to(self.path), y) for y in exclude_patterns]
            )
            ignore = x.name.startswith(".") and ignore_dotfiles
            if x.is_file() and not exclude and not ignore:
                yield x
            else:
                continue


def open_as_dicom(path):
    """Tries to open path as dicom

    Parameters
    ----------
    path: Pathlike
        Path a to a file

    Returns
    -------
    pydicom.dataset
        If path can be opened as dicom
    None
        If path cannot be opened
    """
    # sleep(0.2)
    try:
        return pydicom.dcmread(str(path))
    except InvalidDicomError:
        return None
