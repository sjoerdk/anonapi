"""Functions to filter and select files from folders.

Useful for example for selecting only DICOM files in a folder containing all kinds of files
"""
from copy import copy
from pathlib import Path

import pydicom
from pydicom.errors import InvalidDicomError


class SelectionFolder:
    """Selects and filters files
    """
    def __init__(self, path):
        self.path = path

    @staticmethod
    def get_all_file_paths(folder):
        """Get all dicom files from this folder

        Parameters
        ----------
        folder: Pathlike
            Check only files in this folder

        Returns
        -------
        List[Path]
            Full path to all paths in folder

        """
        folder = Path(folder)
        return [x for x in folder.glob("**/*") if x.is_file()]


class SelectionFolderFileList:
    """List of files that can be iterated over to check two things: whether they are dicom files and whether they have
    consistent PatientID and StudyInstanceUID
    """

    def __init__(self, paths):
        self.paths_to_process = copy(paths)
        self.paths_processed = []
        self.paths_selected = []

        self.last_pid = None
        self.last_suid = None

    def __iter__(self):
        return self

    def __len__(self):
        return len(self.paths_to_process)

    def __next__(self):
        if not self.paths_to_process:
            raise StopIteration
        else:
            path = self.paths_to_process.pop()
            ds = self.load_as_dicom(path)
            if ds:
                try:
                    self.check_dicom(ds)
                except InconsistentDICOM as e:
                    msg = f"Error in '{path}': {e}"
                    raise InconsistentDICOM(msg)

                self.paths_selected.append(path)
            self.paths_processed.append(path)
            return path

    def check_dicom(self, ds):
        """
        Parameters
        ----------
        ds: pydicom.dataset.DataSet
            DICOM Dataset to check

        Raises
        ------
        InconsistentDICOM
        When PatientID or StudyInstanceUID differs from last dataset

        """
        current_pid = ds['PatientID'].value
        current_suid = ds['StudyInstanceUID'].value

        if not self.last_pid:
            self.last_pid = current_pid
        if not self.last_suid:
            self.last_suid = current_suid

        if not self.last_pid == current_pid:
            raise InconsistentDICOM(f"PatientID '{current_pid}' does not match previous value '{self.last_pid}'")
        if not self.last_suid == current_suid:
            raise InconsistentDICOM(f"StudyInstanceUID '{current_suid}' does not match previous value '{self.last_suid}'")

    @staticmethod
    def load_as_dicom(path):
        """

        Parameters
        ----------
        path: Pathlike
            Path to load as dicom

        Returns
        -------
        pydicom.dataset.DataSet
        If file could be loaded as dicom

        None
        If file could not be loaded as dicom
        """
        try:
            ds = pydicom.dcmread(str(path))
        except InvalidDicomError:
            ds = None
        return ds


class SelectionException(Exception):
    pass


class InconsistentDICOM(SelectionException):
    pass
