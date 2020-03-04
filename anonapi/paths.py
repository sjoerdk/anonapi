"""For mapping local paths to UNC paths

Paths in IDIS are tricky. Data coming from 'H:\some_path' locally cannot
be found by the servers under that name. Instead only UNC paths like
'\\servername\share\some_path' should be used. But there is no easy way
to make this connection because of several reasons
* In windows, network drive mappings are very hard to obtain programatically,
  requiring specialised modules
* A local disk might not even be accessible as a unc path

In the end we just need to ditch local network drives altogether in favor of either
file transfer via https, or perhaps doing the processing locally.

In the mean time, solving this by just having a user-defined mapping.
"""
import collections
from pathlib import Path, PureWindowsPath, PurePath
from typing import Dict, List


class UNCPath(PureWindowsPath):
    r"""A UNC path like \\server\share\file

    Notes
    -----
    Only an approximation. Looking into what constitutes a *real* UNC path
    uncovered a pile of dirt and long long regex strings. This class is
    content to catch most non-UNC paths.
    """

    def __init__(self, path=Path):
        super().__init__()
        if not self.is_unc(path):
            raise ValueError(f"{path} is not a UNC path")
        self.path = path

    @staticmethod
    def is_unc(path: Path) -> bool:
        return PureWindowsPath(path).anchor.startswith(r"\\")


class UNCMap:
    """A mapping between one local path and a unc path"""
    def __init__(self, local: Path, unc: UNCPath):
        self.local = local
        self.unc = unc


class UNCMapping:
    """Translates paths between local and UNC"""

    def __init__(self, mapping: List[UNCMap]):
        self.mapping = mapping

    def to_unc(self, path: Path) -> UNCPath:
        # see whether local path starts any of the mapped ones
        pass

    def to_local(self, unc_path: UNCPath) -> Path:
        pass
