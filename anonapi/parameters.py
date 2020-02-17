"""Parameters that are used to create jobs. Some are quite simple, like 'description'
which is just a string. Others are more complex, such as 'source' which has its own
type family and validation.

Put these in separate module because rows appear in several guises throughout
the job creation process and I want a unified type

"""
from copy import copy
from typing import List, Optional

from anonapi.exceptions import AnonAPIException
from fileselection.fileselection import FileSelectionFile
from pathlib import Path, PureWindowsPath


class SourceIdentifier:
    """A string representing a place where data is coming from

    Attributes
    ----------
    key: str
        Class level attribute to identify this class of identifiers
    identifier: str
        Instance level attribute giving the actual value for this identifier.
        For example a specific root_path or UID
    """

    key = "base"  # key with which this class is identified

    def __init__(self, identifier):
        self.identifier = identifier

    def __str__(self):
        return f"{self.key}:{self.identifier}"

    @classmethod
    def cast_to_subtype(cls, identifier):
        """Try to figure out which subtype of source identifier this is and return
        object of that type

        Parameters
        ----------
        identifier, str
            Valid source identifier, like 'root_path:/tmp/'

        Raises
        ------
        UnknownSourceIdentifierException
            When source identifier is not recognized

        """
        return SourceIdentifierFactory().get_source_identifier_for_key(identifier)


class PathIdentifier(SourceIdentifier):
    @property
    def path(self) -> Path:
        return self.identifier

    @path.setter
    def path(self, value):
        self.identifier = value


class FolderIdentifier(PathIdentifier):
    """Refers to a complete folder
    """

    key = "folder"


class FileSelectionIdentifier(PathIdentifier):
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
        with open(self.identifier, "r") as f:
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
        FolderIdentifier,
        StudyInstanceUIDIdentifier,
        AccessionNumberIdentifier,
        FileSelectionIdentifier,
    ]

    def get_source_identifier_for_key(self, key):
        """Cast given key string back to identifier object

        Parameters
        ----------
        key: str
            Key to cast, like 'folder:/myfolder'

        Raises
        ------
        UnknownSourceIdentifierException:
            When the key cannot be cast to any known identifier

        Returns
        -------
        Instance of SourceIdentifier or subtype
            The type that the given key represents
        """
        try:
            type_key, identifier = key.split(":", maxsplit=1)
        except ValueError as e:
            msg = (
                f"'{key}' is not a valid source. There should be a single colon"
                f" ':' sign somewhere. "
                f"Original error: {e}"
            )
            raise UnknownSourceIdentifierException(msg)

        for id_type in self.types:
            if id_type.key == type_key:
                return id_type(identifier=identifier)

        raise UnknownSourceIdentifierException(
            f"Unknown identifier '{key}'. Known identifiers: "
            f"{[x.key for x in self.types]}"
        )

    def get_source_identifier_for_obj(self, object_in):
        """Generate an identifier for a given object

        Parameters
        ----------
        object_in: obj
            Object instance to get identifier for

        Raises
        ------
        UnknownObjectException:
            When no identifier can be created for this object

        Returns
        -------
        SourceIdentifier or subtype
            Idenfitier for the given object
        """
        # get all indentifier types that can handle translation to and from objects
        object_types = [x for x in self.types if hasattr(x, "associated_object_class")]

        object_identifier_class = None
        for x in self.types:
            try:
                if x.associated_object_class == type(object_in):
                    object_identifier_class = x
                    break
            except AttributeError:
                continue
        if not object_identifier_class:
            raise UnknownObjectException(
                f"Unknown object: {object_in}. I can't create an" f"identifier for this"
            )

        return object_identifier_class.from_object(object_in)


class Parameter:
    """A typed, human readable,  persistable key-value pair that means something
    in anonapi

    Made this because the mapping csv file contains rows in different
    forms. I still want to treat them the same
    """

    field_name = "parameter"
    description = "Parameter base type"

    def __init__(self, value: str = None):
        if not value:
            value = ""
        self.value = str(value)

    def __str__(self):
        return f"{self.field_name},{self.value}"


class PatientID(Parameter):
    field_name = "patient_id"
    description = "Patient ID to set in anonymized data"


class PatientName(Parameter):
    field_name = "patient_name"
    description = "Patient Name to set in anonymized data"


class Description(Parameter):
    field_name = "description"
    description = "Job description, free text"


class PIMSKey(Parameter):
    field_name = "pims_key"
    description = "Use this PIMS project to pseudonymize"


class Project(Parameter):
    field_name = "project"
    description = "Anonymize according to this project"


class PathParameter(Parameter):
    """A parameter that can refer to a root_path on disk or share

    Always has a 'path' property that can get and set the path part
    """

    description = "A parameter describing a path"

    def __init__(self, value: PureWindowsPath = None):
        super(PathParameter, self).__init__()
        if value:
            self.value = PureWindowsPath(value)
        else:
            self.value = PureWindowsPath()

    @property
    def path(self) -> PureWindowsPath:
        return self.value

    def as_absolute(self, root_path: Path):
        """A copy of this parameter but with an absolute root path"""
        if self.path.is_absolute():
            try:
                self.path.relative_to(root_path)
            except ValueError as e:
                raise ParameterException(f"Cannot make this absolute '{e}'")
        else:
            return type(self)(root_path / self.path)


class DestinationPath(PathParameter):
    field_name = "destination_path"
    description = "Write data to this UNC path after anonymization"


class RootSourcePath(PathParameter):
    field_name = "root_source_path"
    description = "Path sources are all relative to this UNC path"


class SourceIdentifierParameter(PathParameter):
    """Reference to the source of the data"""

    field_name = "source"
    description = "Data to anonymize comes from this source"

    def __init__(self, value: str):
        """

        Parameters
        ----------
        value: str
            Valid source identifier string

        """
        super(SourceIdentifierParameter, self).__init__()
        self.value = SourceIdentifierFactory().get_source_identifier_for_key(str(value))

    @property
    def path(self) -> Optional[Path]:
        """Return the path part of this identifier. """
        try:
            return Path(self.value.path)
        except AttributeError:  # identifier might be non-path, like a PACS uid
            return None

    @path.setter
    def path(self, value):
        if hasattr(self.value, "path"):
            self.value.path = value
        else:
            raise AttributeError(f"{self.value} has no attribute 'Path'")

    def as_absolute(self, root_path: Path):
        """A copy of this parameter but with an absolute oot path"""
        if not self.path:
            # no path to do anything to. just return a copy
            return SourceIdentifierParameter(copy(self.value))
        else:
            if self.path.is_absolute():
                try:
                    self.path.relative_to(root_path)
                except ValueError as e:
                    raise ParameterException(f"Cannot make this absolute '{e}'")
            else:
                identifier_copy = copy(self.value)
                identifier_copy.path = root_path / identifier_copy.path
                return SourceIdentifierParameter(identifier_copy)


class ParameterFactory:
    """Knows about all sort of rows and can convert between string and object
    representation"""

    @classmethod
    def parse_from_string(cls, string):
        """

        Parameters
        ----------
        string: str
            A valid string representation of Parameter

        Returns
        -------
        Parameter
            An instance, instantiated with a value, if any was found in the string

        Raises
        ------
        ParameterParsingError
            If the string cannot be parsed as any known parameter

        """
        try:
            key, value = string.split(",", maxsplit=1)
        except ValueError:
            raise ParameterParsingError(
                f"Could not split '{string}' into key and value. There should be a "
                f"comma somewhere."
            )
        return cls.parse_from_key_value(key=key, value=value)

    @classmethod
    def parse_from_key_value(cls, key, value):
        for param_type in ALL_PARAMETERS:
            if param_type.field_name == key:
                try:
                    return param_type(value)
                except UnknownSourceIdentifierException as e:
                    raise ParameterParsingError(f"Error parsing source identifier:{e}")
        raise ParameterParsingError(
            f"Could not parse key={key}, value={value} to any known parameter. "
            f"Tried {[x.field_name for x in ALL_PARAMETERS]}"
        )


class ParameterSet:
    """A collection of parameters with some convenient methods for checking
    existence of specific parameters etc..

    """

    def __init__(
        self, parameters: List[Parameter], default_parameters: List[Parameter] = None
    ):
        """

        Parameters
        ----------
        parameters: List[Parameter]
            The parameters in this set
        default_parameters: List[Parameter]
            Include these parameters, unless overwritten in parameters
        """
        if not default_parameters:
            default_parameters = []
        param_dict = {type(x): x for x in default_parameters}
        param_dict.update({type(x): x for x in parameters})
        self.parameters = list(param_dict.values())

    def get_param_by_type(self, type_in) -> Optional[Parameter]:
        """Return the first Parameter instance that is (or derives from) type
         or None"""
        return next((x for x in self.parameters if isinstance(x, type_in)), None)

    def get_params_by_type(self, type_in) -> List[Parameter]:
        """Return all parameters that are type or subtype, or empty list"""
        return [x for x in self.parameters if isinstance(x, type_in)]

    @staticmethod
    def is_source_identifier(parameter):
        """A parameter that indicates the source of the data for an anon job"""
        return isinstance(parameter, SourceIdentifierParameter)

    @staticmethod
    def is_path_type(parameter):
        """Refers to data coming from a share or disk"""
        return any(
            isinstance(parameter.value, x)
            for x in [FolderIdentifier, FileSelectionIdentifier]
        )

    @staticmethod
    def is_pacs_type(parameter):
        """Refers to data coming from the PACS system"""
        return isinstance(parameter.value, PACSResourceIdentifier)


def is_unc_path(path: Path):
    """Is this a unc path like \\server\share\things? """

    return PureWindowsPath(path).anchor.startswith(r"\\")


COMMON_JOB_PARAMETERS = [SourceIdentifierParameter, PatientID, PatientName, Description]
COMMON_GLOBAL_PARAMETERS = [PIMSKey, DestinationPath, RootSourcePath, Project]

ALL_PARAMETERS = COMMON_JOB_PARAMETERS + COMMON_GLOBAL_PARAMETERS


class ParameterException(AnonAPIException):
    pass


class ParameterParsingError(ParameterException):
    pass


class UnknownSourceIdentifierException(ParameterException):
    pass


class UnknownObjectException(ParameterException):
    pass
