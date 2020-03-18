r"""For maps local paths to UNC paths

Paths in IDIS are tricky. Data coming from 'H:\some_path' locally cannot
be found by the servers under that name. Instead only UNC paths like
'\\servername\share\some_path' should be used. But there is no easy way
to make this connection because of several reasons
* In windows, network drive mappings are very hard to obtain programatically,
  requiring specialised modules
* A local disk might not even be accessible as a unc path

In the end we just need to ditch local network drives altogether in favor of either
file transfer via https or perhaps doing the processing locally.

In the mean time, solving this by just having a user-defined maps.
"""
import collections
from pathlib import Path, PureWindowsPath, PurePath
from typing import Dict, List

from anonapi.exceptions import AnonAPIException


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
    """A maps between one local path and a unc path"""
    def __init__(self, local: Path, unc: UNCPath):
        self.local = local
        self.unc = unc


class UNCMapping:
    r"""Translates paths between local and UNC

    Conversion has the following properties:
    * Re-converting already converted is allowed. convert(convert(x)) = convert(x)
    * If no conversion is needed, input is returned as is. to_unc(unc) = unc

    Sidestepping the path marsh with simplistic defintions of UNC and local:
    * 'UNC path' : anything with an anchor that starts with \\
    * 'local path': anything that is not UNC path
    """

    def __init__(self, maps: List[UNCMap]):
        self.maps = maps

    def to_unc(self, path_in: Path) -> UNCPath:
        """Convert the given path to a UNC path
        
        Parameters
        ----------
        path_in: Path
            Any path

        Returns
        -------
        UNCPath
            Input path as a UNC path. Searches internal list of maps
        
        Raises
        ------
        UNCMappingException
            If path cannot be mapped any UNC path 

        """
        if UNCPath.is_unc(path_in):
            return path_in  # is it a UNC path already? Then return as is

        for map_in in self.maps:   # try each map
            try:
                return map_in.unc / path_in.relative_to(map_in.local)
            except ValueError:
                continue

        raise UNCMappingException(f'{path_in} could not be mapped to UNC path.'
                                  f' I know only {[x.local for x in self.maps]}')

    def to_local(self, path_in: Path) -> Path:
        """Convert the given path to a local path

        Parameters
        ----------
        path_in: Path
            Any path

        Returns
        -------
        Path
            Input path as local path

        Raises
        ------
        UNCMappingException
            If path cannot be mapped any local path

        """

        if not UNCPath.is_unc(path_in):
            return path_in  # if path is not UNC, assume it's local and return as is

        for map_in in self.maps:
            try:
                return map_in.local / path_in.relative_to(map_in.unc)
            except ValueError:
                continue
        raise UNCMappingException(f'{path_in} could not be mapped to local path.'
                                  f' I know only {[x.unc for x in self.maps]}')


class UNCMappingException(AnonAPIException):
    pass
