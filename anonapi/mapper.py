"""Makes it possible to map source files to anonymized id, name etc. Pre-processing step for creating IDIS jobs

Meant to be usable in a command line, with minimal windows editing tools. Maybe Excel, maybe notepad

"""
import csv
import os
import platform
import subprocess
from collections import UserDict
from os import path
from pathlib import Path


class SourceIdentifier:
    """A string representing a place where data is coming from

    """

    key = "base"

    def __init__(self, identifier):
        self.identifier = identifier

    def __str__(self):
        return f"{self.key}:{self.identifier}"


class FileSelectionIdentifier(SourceIdentifier):
    """A file selection in a specific folder
    """

    key = "folder"


class SourceIdentifierFactory:
    """Creates SourceIdentifier objects based on key string
    """

    types = [SourceIdentifier, FileSelectionIdentifier]

    def get_source_identifier(self, key):
        """Cast given key string back to identifier object

        Parameters
        ----------
        key: str
            Key to cast, like 'folder:/myfolder'

        Raises
        ------
        UnknownSourceIdentifier:
            When the key cannot be cast to any known identifier

        Returns
        -------
        SourceIdentifier or subtype
        The type that the given key represents
        """
        try:
            type_key, identifier = key.split(":")
        except ValueError as e:
            msg = (
                f"'{key}' is not a valid source. There should be a single colon ':' sign somewhere. "
                f"Original error: {e}"
            )
            raise UnknownSourceIdentifier(msg)

        for id_type in self.types:
            if id_type.key == type_key:
                return id_type(identifier=identifier)

        raise UnknownSourceIdentifier(
            f"Unknown identifier '{key}'. Known identifiers: {[x.key for x in self.types]}"
        )


class AnonymizationParameters:
    """Settings that can be set when creating a job and that are likely to change within a single mapping

    """

    PATIENT_ID_NAME = "patient_id"
    PATIENT_NAME = "patient_name"
    DESCRIPTION_NAME = "description"

    field_names = [PATIENT_ID_NAME, PATIENT_NAME, DESCRIPTION_NAME]

    def __init__(self, patient_id, patient_name=None, description=None):
        self.patient_id = patient_id
        self.patient_name = patient_name
        self.description = description

    def as_dict(self, parameters_to_include=None):
        """

        Parameters
        ----------
        parameters_to_include: List[str], optional
            List of strings from AnonymizationParameters.field_names. Defaults to all parameters

        Returns
        -------

        """
        if parameters_to_include:
            for param in parameters_to_include:
                if param not in AnonymizationParameters.field_names:
                    raise ValueError(
                        f"Unknown parameter '{param}'. Allowed: {AnonymizationParameters.field_names}"
                    )

        all_values = {
            self.PATIENT_ID_NAME: self.patient_id,
            self.PATIENT_NAME: self.patient_name,
            self.DESCRIPTION_NAME: self.description,
        }
        if parameters_to_include:
            return {
                key: value
                for key, value in all_values.items()
                if key in parameters_to_include
            }
        else:
            return all_values


class MappingList(UserDict):
    """List of mappings that can be read from and saved to disk

    """

    DEFAULT_FILENAME = "anon_mapping.csv"

    def __init__(self, mapping):
        """

        Parameters
        ----------
        mapping: Dict[SourceIdentifier, AnonymizationParameters]
            Initialize mapping with this dicts

        """
        self.data = mapping

    def save(self, f, parameters_to_write=AnonymizationParameters.field_names):
        """

        Parameters
        ----------
        f: stream
            Write to this
        parameters_to_write: List[str], optional
            List of strings from AnonymizationParameters.field_names. Defaults to all parameters

        """

        writer = csv.DictWriter(
            f,
            delimiter=",",
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL,
            fieldnames=["source"] + parameters_to_write,
        )
        writer.writeheader()
        for identifier, parameters in self.data.items():
            fields = {
                "source": str(identifier),
                **parameters.as_dict(parameters_to_include=parameters_to_write),
            }
            writer.writerow(fields)

    @classmethod
    def load(cls, f):
        """Load a MappingList instance from open file handle

        Parameters
        ----------
        f
            file object opened for reading

        Returns
        -------
        MappingList
            Loaded from data in f

        Raises
        ------
        MappingLoadError:
            If mapping could not be loaded

        """
        reader = csv.DictReader(f)
        id_factory = SourceIdentifierFactory()
        mapping = {}
        for row in reader:
            try:
                source = id_factory.get_source_identifier(row["source"])
            except KeyError as e:
                raise MappingLoadError(
                    f"Could not find column with header 'source'. This is required."
                )
            # It might be that not all parameters have been written. Set these to None
            parameters = {
                "patient_id": row.get(AnonymizationParameters.PATIENT_ID_NAME, None),
                "patient_name": row.get(AnonymizationParameters.PATIENT_NAME, None),
                "description": row.get(AnonymizationParameters.DESCRIPTION_NAME, None),
            }
            mapping[source] = AnonymizationParameters(**parameters)
        return cls(mapping)

    def to_table_string(self):
        """A source - patient_id table with a small header

        Returns
        -------
        str:
            Nice string representation of this list, 80 chars wide, truncated if needed

        """

        header = (
            f"Mapping with {len(self)} entries\n"
            "source                                             patient_id\n"
            "--------------------------------------------------------------------------------"
        )
        info_string = header

        for x, y in self.items():
            info_line = f"{str(x)[-40:]:<50} {y.patient_id[-40:]:<30} "
            info_string += "\n" + info_line

        return info_string


class MappingListFolder:
    """Folder that might contain a mapping list.

    Uses a single default filename that it expects mapping list to be saved under.

    """

    DEFAULT_FILENAME = "anon_mapping.csv"

    def __init__(self, folder_path):
        """

        Parameters
        ----------
        path: Pathlike
            path to this folder
        """
        self.folder_path = Path(folder_path)

    def full_path(self):
        return self.folder_path / self.DEFAULT_FILENAME

    def has_mapping_list(self):
        """Is there a default mapping list defined in this folder?"""
        return self.full_path().exists()

    def save_list(self, mapping_list: MappingList):
        with open(self.full_path(), 'w') as f:
            mapping_list.save(f)

    def load_list(self):
        """

        Returns
        -------

        """
        with open(self.full_path(), 'r') as f:
            return MappingList.load(f)

    def delete_list(self):
        os.remove(self.full_path())


def get_example_mapping_list():
    mapping = {
        FileSelectionIdentifier(
            identifier=path.sep.join(["example", "folder1"])
        ): AnonymizationParameters(
            patient_name="Patient1", patient_id="12345", description="An optional description for patient 1"
        ),
        FileSelectionIdentifier(
            identifier=path.sep.join(["example", "folder2"])
        ): AnonymizationParameters(
            patient_name="Patient2",
            patient_id="23456",
            description="An optional description for patient 2",
        ),
    }
    return MappingList(mapping=mapping)


def open_mapping_in_editor(mapping_file):
    print(f"Opening {mapping_file}")
    open_file_in_default_editor(mapping_file)


def open_file_in_default_editor(mapping_file):
    if platform.system() == 'Linux':
        subprocess.Popen(args=['xdg-open', mapping_file])
    elif platform.system() == 'Windows':
        subprocess.Popen(['start', mapping_file], shell=True)
    else:
        raise NotImplemented(f"Opening new terminal not supported on platform '{platform.system()}'")


class MapperException(Exception):
    pass


class UnknownSourceIdentifier(MapperException):
    pass


class MappingLoadError(MapperException):
    pass
