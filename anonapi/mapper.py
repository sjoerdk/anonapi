"""Makes it possible to map source files to anonymized id, name etc.
Pre-processing step for creating IDIS jobs

Meant to be usable in a command line, with minimal windows editing tools. Maybe
Excel, maybe notepad

"""
import csv
import os
from collections import UserDict
from os import path
from pathlib import Path

from fileselection.fileselection import FileSelectionFile


class SourceIdentifier:
    """A string representing a place where data is coming from

    Attributes
    ----------
    key: str
        Class level attribute to identify this class of identifiers
    identifier: str
        Instance level attribute giving the actual value for this identifier.
        For example a specific path or UID
    """

    key = "base"  # key with which this class is identified

    def __init__(self, identifier):
        self.identifier = identifier

    def __str__(self):
        return f"{self.key}:{self.identifier}"


class PathIdentifier(SourceIdentifier):
    """Refers to a path
    """

    key = "path"

    def __init__(self, identifier):
        """

        Parameters
        ----------
        identifier: pathlike
        """
        super().__init__(Path(identifier))


class ObjectIdentifier(SourceIdentifier):
    """An identifier that can be translated from and to a python object

    """
    associated_object_class = None

    @classmethod
    def from_object(cls, object):
        """

        Returns
        -------
        ObjectIdentifier instance or child of ObjectIdentifier instance
        """
        raise NotImplemented

    def to_object(self):
        """
        Returns
        -------
        instance of self.object_class corresponding to this identifier
        """


class FileSelectionFolderIdentifier(PathIdentifier):
    """A file selection in a specific folder. Selection file name is default.
    Folder can be relative or absolute
    """

    key = "folder"


class FileSelectionIdentifier(PathIdentifier, ObjectIdentifier):
    """A file selection in a specific file
    """

    key = "fileselection"
    associated_object_class = FileSelectionFile

    @classmethod
    def from_object(cls, object: FileSelectionFile):
        return cls(identifier=object.data_file_path)

    def to_object(self):
        """

        Returns
        -------
        FileSelectionFile

        Raises
        ------
        FileNotFoundError
            When the fileselection file cannot be found on local disk

        """
        with open(self.identifier, 'r') as f:
            return FileSelectionFile.load(f, datafile=self.identifier)


class PACSResourceIdentifier(SourceIdentifier):
    """A key to for some object in a PACS system

    """

    key = "pacs_resource"


class StudyInstanceUIDIdentifier(PACSResourceIdentifier):
    """a DICOM StudyInstanceUID
    """

    key = "study_instance_uid"


class AccessionNumberIdentifier(PACSResourceIdentifier):
    """A DICOM AccessionNumber
    """

    key = "accession_number"


class SourceIdentifierFactory:
    """Creates SourceIdentifier objects based on key string
    """

    types = [
        SourceIdentifier,
        FileSelectionFolderIdentifier,
        StudyInstanceUIDIdentifier,
        AccessionNumberIdentifier,
        FileSelectionIdentifier
    ]

    def get_source_identifier_for_key(self, key):
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
                f"'{key}' is not a valid source. There should be a single colon"
                f" ':' sign somewhere. "
                f"Original error: {e}"
            )
            raise UnknownSourceIdentifier(msg)

        for id_type in self.types:
            if id_type.key == type_key:
                return id_type(identifier=identifier)

        raise UnknownSourceIdentifier(
            f"Unknown identifier '{key}'. Known identifiers: {[x.key for x in self.types]}"
        )

    def get_source_identifier_for_obj(self, object):
        """Generate an identifier for a given object

        Parameters
        ----------
        object: obj
            Object instance to get identifier for

        Raises
        ------
        UnknownObject:
            When no identifier can be created for this object

        Returns
        -------
        SourceIdentifier or subtype
            Idenfitier for the given object
        """
        # get all indentifier types that can handle translation to and from objects
        object_types = \
            [x for x in self.types if hasattr(x, 'associated_object_class')]

        object_identifier_class = None
        for x in self.types:
            try:
                if x.associated_object_class == type(object):
                    object_identifier_class = x
                    break
            except AttributeError:
                continue
        if not object_identifier_class:
            raise UnknownObject(f"Unknown object: {object}. I can't create an"
                                f"identifier for this")

        return object_identifier_class.from_object(object)


class AnonymizationParameters:
    """Settings that can be set when creating a job and that are likely to
    change within a single mapping

    """

    PATIENT_ID_NAME = "patient_id"
    PATIENT_NAME = "patient_name"
    DESCRIPTION_NAME = "description"
    PIMS_KEY = "pims_key"

    field_names = [PATIENT_ID_NAME, PATIENT_NAME, DESCRIPTION_NAME, PIMS_KEY]

    def __init__(
        self, patient_id=None, patient_name=None, description=None, pims_key=None
    ):
        self.patient_id = patient_id
        self.patient_name = patient_name
        self.description = description
        self.pims_key = pims_key

    def as_dict(self, parameters_to_include=None):
        """

        Parameters
        ----------
        parameters_to_include: List[str], optional
            List of strings from AnonymizationParameters.field_names. Defaults
            to all parameters

        Returns
        -------

        """
        if parameters_to_include:
            for param in parameters_to_include:
                if param not in AnonymizationParameters.field_names:
                    raise ValueError(
                        f"Unknown parameter '{param}'. "
                        f"Allowed: {AnonymizationParameters.field_names}"
                    )

        all_values = {
            self.PATIENT_ID_NAME: self.patient_id,
            self.PATIENT_NAME: self.patient_name,
            self.DESCRIPTION_NAME: self.description,
            self.PIMS_KEY: self.pims_key,
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
            Initialize mapping with these dicts

        """
        self.data = mapping

    def save(self, f, parameters_to_write=AnonymizationParameters.field_names):
        """

        Parameters
        ----------
        f: stream
            Write to this
        parameters_to_write: List[str], optional
            List of strings from AnonymizationParameters.field_names.
            Defaults to all parameters

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
                source = id_factory.get_source_identifier_for_key(row["source"])
            except KeyError as e:
                raise MappingLoadError(
                    f"Could not find column with header 'source'. This is required."
                )
            # Read in parameters. If they are missing from input set them to None
            parameters = {
                x: row.get(x, None) for x in AnonymizationParameters.field_names
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

    def make_relative(self, path):
        """Make the given path relative to this mapping folder

        Parameters
        ----------
        path: Pathlike

        Returns
        -------
        Path
            Path relative to this mapping folder

        Raises
        ------
        MapperException
            When path cannot be made relative

        """
        path = Path(path)
        if not path.is_absolute():
            return path
        try:
            return path.relative_to(self.folder_path)
        except ValueError as e:
            raise MapperException(f"Error making path relative: {e}")

    def make_absolute(self, path):
        """Get absolute path to the given path, assuming it is in this mapping folder

        Parameters
        ----------
        path: Pathlike

        Returns
        -------
        Path
            Absolute path, assuming mapping folder as base folder

        Raises
        ------
        MapperException
            When given path is already absolute

        """
        path = Path(path)
        if path.is_absolute():
            raise MapperException("Cannot make absolute path absolute")
        return self.folder_path / Path(path)

    def has_mapping_list(self):
        """Is there a default mapping list defined in this folder?"""
        return self.full_path().exists()

    def save_list(self, mapping_list: MappingList):
        with open(self.full_path(), "w") as f:
            mapping_list.save(f)

    def load_list(self):
        """

        Returns
        -------

        """
        with open(self.full_path(), "r") as f:
            return MappingList.load(f)

    def delete_list(self):
        os.remove(self.full_path())

    def get_mapping(self):
        """Load default mapping from this folder

        Returns
        -------
        MappingList
            Loaded from current dir

        Raises
        ------
        MappingLoadError
            When no mapping could be loaded from current directory

        """

        try:
            with open(self.full_path(), "r") as f:
                return MappingList.load(f)
        except FileNotFoundError:
            raise MappingLoadError("No mapping defined in current directory")
        except MapperException as e:
            raise MappingLoadError(f"Error loading mapping: {e}")


def get_example_mapping_list():
    mapping = {
        FileSelectionFolderIdentifier(
            identifier=path.sep.join(["example", "folder1"])
        ): AnonymizationParameters(
            patient_name="Patient1",
            patient_id="12345",
            description="An optional description for patient 1",
        ),
        FileSelectionFolderIdentifier(
            identifier=path.sep.join(["example", "folder2"])
        ): AnonymizationParameters(
            patient_name="Patient2",
            patient_id="23456",
            description="An optional description for patient 2",
        ),
    }
    return MappingList(mapping=mapping)


class ExampleMappingList(MappingList):
    """A mapping list with some example content. Gives an overview of possible
     identifiers

    """

    def __init__(self):
        mapping = {
            FileSelectionFolderIdentifier(
                identifier=path.sep.join(["example", "folder1"])
            ): AnonymizationParameters(
                patient_name="Patient1",
                patient_id="001",
                description="All files from folder1",
            ),
            StudyInstanceUIDIdentifier(
                "123.12121212.12345678"
            ): AnonymizationParameters(
                patient_name="Patient2",
                patient_id="002",
                description="A study which should be retrieved from PACS, "
                            "identified by StudyInstanceUID",
            ),
            AccessionNumberIdentifier("12345678.1234567"): AnonymizationParameters(
                patient_name="Patient3",
                patient_id="003",
                description="A study which should be retrieved from PACS, "
                            "identified by AccessionNumber",
            ),
            FileSelectionIdentifier(
                Path("folder2/fileselection.txt")): AnonymizationParameters(
                    patient_name="Patient4", patient_id="004",
                    description="A selection of files in folder2")
        }
        super().__init__(mapping=mapping)


class MapperException(Exception):
    pass


class UnknownSourceIdentifier(MapperException):
    pass


class UnknownObject(MapperException):
    pass


class MappingLoadError(MapperException):
    pass
