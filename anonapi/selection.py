"""Functions to filter and select files from folders.
Useful for example for selecting only DICOM files in a folder.
"""
from pathlib import Path

import pydicom
from pydicom.errors import InvalidDicomError


class DICOMFileFolder:
    """A folder that might contains at least some dicom files.
    """

    def __init__(self, path):
        self.path = path

    def all_files(self):
        """Iterator that yields all subpaths. Allows progress bar

        Parameters
        ----------
        paths: List[Pathlike]

        Returns
        -------
        generator
            Yields Path if the path is a file, None otherwise

        """
        folder = Path(self.path)
        for x in folder.glob("**/*"):
            if x.is_file():
                yield x
            else:
                yield None

    @staticmethod
    def all_dicom_files(paths):
        """Create an iterator so loading files as dicom can be monitored and a progress bar can be shown

        Parameters
        ----------
        paths: List[Pathlike]

        Returns
        -------
        iterator
            yields pydicom.dataset.DataSet If file could be loaded as dicom,

        """
        return DICOMFileList(paths)


class DICOMFileList:
    def __init__(self, paths):
        """Container of potential DICOM files. Can be used as iterator for trying to open files as DICOM

        Parameters
        ----------
        paths: List[Pathlike]
            paths to try to load as DICOM

        """
        self.paths = paths

    def __len__(self):
        return len(self.paths)

    def __iter__(self):
        """Opens each path in turn. Tries to opens as DICOM

        Returns
        -------
        (Path, pydicom.dataset)
            if path is DICOM
        (Path, None)
            if not

        """
        for path in self.paths:
            try:
                ds = pydicom.dcmread(str(path))
                yield path, ds
            except InvalidDicomError:
                yield path, None
