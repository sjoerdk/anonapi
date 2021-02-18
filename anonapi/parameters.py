"""Parameters that are used to create jobs. Some are quite simple, like 'description'
which is just a input. Others are more complex, such as 'source' which has its own
type family and validation.

Put these in separate module because rows appear in several guises throughout
the job creation process and I want a unified type

"""
import string
import random
from copy import copy
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Type

from anonapi.exceptions import AnonAPIException
from fileselection.fileselection import FileSelectionFile
from pathlib import Path, PureWindowsPath


class SourceIdentifier:
    """An input representing a place where data is coming from

    Attributes
    ----------
    identifier: str
        Instance level attribute giving the actual value for this identifier.
        For example a specific root_path or UID
    """

    key: str = "base"  # key with which this class is identified

    def __init__(self, identifier):
        self.identifier = self.parse_identifier(identifier)

    def __str__(self):
        return f"{self.key}:{self.identifier}"

    @classmethod
    def parse_identifier(cls, identifier: Any) -> Any:
        """Check format, remove clutter. Can be overwritten in child classes

        Returns
        -------
        str
            cleaned identifier input

        Raises
        ------
        ParameterException
            If this identifier does not have the correct format

        """
        if type(identifier) == str:
            return identifier.rstrip()
        else:
            return identifier

    @classmethod
    def cast_to_subtype(cls, identifier):
        """Try to figure out which subtype of source identifier this is and return
        object of that type

        Parameters
        ----------
        identifier: str
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
    """Refers to a complete folder"""

    key = "folder"


class FileSelectionIdentifier(PathIdentifier):
    """A file selection in a specific file"""

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
    """A key to for some object in a PACS system"""

    key = "pacs_resource"


class StudyInstanceUIDIdentifier(PACSResourceIdentifier):
    """a DICOM StudyInstanceUID"""

    key = "study_instance_uid"


class AccessionNumberIdentifier(PACSResourceIdentifier):
    """A DICOM AccessionNumber"""

    key = "accession_number"


class SourceIdentifierFactory:
    """Creates SourceIdentifier objects based on key input"""

    types = [
        SourceIdentifier,
        FolderIdentifier,
        StudyInstanceUIDIdentifier,
        AccessionNumberIdentifier,
        FileSelectionIdentifier,
    ]

    def get_source_identifier_for_key(self, key: str) -> SourceIdentifier:
        """Cast given key input back to identifier object

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
    """A typed, human readable, persistable key-value pair that means something
    in anonapi

    Made this because the mapping csv file contains rows in different
    forms. I still want to treat them the same
    """

    field_name = "parameter"
    description = "Parameter base type"

    # historical names for this parameter. Makes sure older files can still be read
    legacy_field_names: List[str] = []

    def __init__(self, value: str = None):
        if not value:
            value = ""
        self.value = str(value)

    def __str__(self):
        return self.to_string()

    @classmethod
    def field_names(cls) -> List[str]:
        """All field names that this parameter might have, current field name first"""
        return [cls.field_name] + cls.legacy_field_names

    def to_string(self, delimiter=",") -> str:
        """Parameter as string, for serialization

        Separate method from __str__ to allow both comma and colon separators
        """
        return f"{self.field_name}{delimiter}{str(self.value)}"

    def describe(self) -> str:
        """Human readable description of this parameter, with description"""
        return f"{self.field_name}:{self.value} ({self.description})"


class PseudoID(Parameter):
    field_name = "pseudo_id"
    description = "Pseudonym for Patient ID to set in anonymized data"
    legacy_field_names = ["patient_id"]


class PseudoName(Parameter):
    field_name = "pseudo_name"
    description = "Pseudonym for Patient name to set in anonymized data"
    legacy_field_names = ["patient_name"]


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
    """A parameter that can refer to a path on disk or share

    Always has a 'path' property that can get and set the path part
    """

    field_name = "path"
    description = "A parameter describing a path"

    def __init__(self, value: PureWindowsPath = None):
        super().__init__()
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
            Valid source identifier input

        """
        super().__init__()
        self.value = SourceIdentifierFactory().get_source_identifier_for_key(str(value))

    @classmethod
    def init_from_source_identifier(cls, obj: SourceIdentifier):
        """Create a source identifier with the given source

        TODO: rewrite this. This method shows that the whole class tree needs
         rewriting. Why is SourceIdentifier not a Parameter? This makes no sense
         and is very hard to follow. Also. Why is SourceIdentifier a PathParameter
         even though it has non-path children such as StudyInstanceUIDIdentifier?
        """
        base = cls(value="base:empty")  # dummy value just to make __init__ pass..
        base.value = obj
        return base

    @property
    def path(self) -> Optional[Path]:
        """Return the path part of this identifier"""
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


class AccessionNumber(Parameter):
    """An accession number from PACS as a data source"""

    field_name = "accession_number"
    description = "Data to anonymize comes from this accession number"


class ParameterFactory:
    """Knows about all sort of rows and can convert between input and object
    representation
    """

    @classmethod
    def parse_from_string(cls, string_in: str) -> Parameter:
        """Create a Parameter from string. Splits on comma and colon

        Parameters
        ----------
        string_in: str
            A valid input representation of Parameter

        Returns
        -------
        Parameter
            An instance, instantiated with a value, if any was found in the input

        Raises
        ------
        ParameterParsingError
            If the input cannot be parsed as any known parameter

        """
        try:
            key, value = string_in.split(",", maxsplit=1)
        except ValueError:
            try:
                key, value = string_in.split(";", maxsplit=1)
            except ValueError:
                raise ParameterParsingError(
                    f"I don't know what kind of parameter '{string_in}' should be. I"
                    f"Know about the following parameters: "
                    f"{[x.field_name for x in ALL_PARAMETERS]}"
                )
        return cls.parse_from_key_value(key=key, value=value)

    @staticmethod
    def parse_from_key_value(
        key, value, parameter_types: Optional[List[Type[Parameter]]] = None
    ) -> Parameter:
        """Parse a key and value string into a valid Parmameter object

        Parameters
        ----------
        key: str
            Parameter.key value indicating the type of parameter,
            like 'accession_number'
        value: str
            The value of the parameter, like '12345.234343'
        parameter_types: Optional[Type[Parameter]], optional
            List of all Parameter types that will be tried for parsing. Defaults
            to parameter_classes.ALL_PARAMETERS

        Raises
        ------
        ParameterParsingError
            If parsing fails for any reason

        Returns
        -------
        Parameter
            A parameter instance of on of the classes parsed from key, value

        """
        if parameter_types is None:
            parameter_types = ALL_PARAMETERS
        for param_type in parameter_types:
            if key in param_type.field_names():
                try:
                    return param_type(value)
                except UnknownSourceIdentifierException as e:
                    raise ParameterParsingError(f"Error parsing source identifier:{e}")
        raise ParameterParsingError(
            f"Could not parse key={key}, value={value} to any known parameter. "
            f"Tried {[x.field_name for x in ALL_PARAMETERS]}"
        )

    @staticmethod
    def generate_pseudo_name() -> PseudoName:
        """Random pseudonym parameter. 8 characters, like '8GW7FEDQ'"""
        return PseudoName(
            "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
        )

    @staticmethod
    def generate_description() -> Description:
        """Description with curent date. Like 'generated_02_23_2020'"""
        return Description(f"generated_" f"{datetime.today().strftime('%B_%d_%Y')}")


class ParameterSet:
    """Contains at most one instance of each parameter type. Allows questions like
    'does this set contain a parameter of type X'. Also offers methods for updating
    one set with another based on types
    """

    def __init__(self, parameters: List[Parameter]):
        """

        Parameters
        ----------
        parameters: List[Parameter]
            The parameters in this set
        """
        self.parameters = parameters

    def __iter__(self):
        return iter(self.parameters)

    def update(self, other: "ParameterSet"):
        """Like dict.update(other). Add new parameters from other. If a parameter
        already exists, overwrite with value from other
        """
        param_dict = {type(x): x for x in self.parameters}
        param_dict.update({type(x): x for x in other})
        self.parameters = list(param_dict.values())

    def get_param_by_type(self, type_in: Type[Parameter]) -> Optional[Parameter]:
        """Return the first Parameter instance that is (or derives from) type
        or None
        """
        return next((x for x in self.parameters if isinstance(x, type_in)), None)

    def get_params_by_type(self, type_in) -> List[Parameter]:
        """Return all parameters that are type or subtype, or empty list"""
        return [x for x in self.parameters if isinstance(x, type_in)]

    def get_source_parameter(self) -> SourceIdentifierParameter:
        """Get the first parameter indicating a data source from this set

        Returns
        -------
        SourceIdentifierParameter

        Raises
        ------
        ParameterException
            If there is no source identifier in this set
        """
        try:
            return next(x for x in self.parameters if self.is_source_identifier(x))
        except StopIteration:
            raise ParameterException(f"No source parameter found in {self.parameters}")

    def split_parameter(
        self, type_in: Type[Parameter]
    ) -> Tuple[Parameter, List[Parameter]]:
        """Split this set into (the first) instance of parameter and rest.

        Returns
        -------
        Tuple[Parameter,List[Parameter]]

        Raises
        ------
        ParameterException
            If no isntance of type_in can be found
        """
        param = self.get_param_by_type(type_in=type_in)
        rest = [x for x in self.parameters if not x == param]

        return param, rest

    def split_source_parameter(
        self,
    ) -> Tuple[SourceIdentifierParameter, List[Parameter]]:
        """Split this set into (the first) source parameter and rest.

        Useful for creating jobs. A missing source parameter is often a deal breaker,
        while other parameters are often optional

        Returns
        -------
        Tuple[SourceIdentifierParameter,List[Parameter]]

        Raises
        ------
        ParameterException
            If no source parameter can be found
        """
        return self.split_parameter(type_in=SourceIdentifierParameter)

    def as_dict(self) -> Dict[str, Parameter]:
        """Dictionary {field name: Parameter with this field_name}. Makes it easier
        to retrieve a parameter of a specific type

        """
        return {x.field_name: x for x in self.parameters}

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
    r"""Is this a unc path like \\server\share\things?"""

    return PureWindowsPath(path).anchor.startswith(r"\\")


def get_legacy_idis_value(identifier: SourceIdentifier) -> str:
    """Give the value for source_instance_id that IDIS understands

    For historical reasons, StudyInstanceUIDs are given without prepended key.
    This should change. For now just do this conversion.
    Example:
    StudyInstanceUID should be parsed as "123.4.5.15.5.56",
    but AccessionNumber should be parsed as "accession_number:1234567.3434636"


    Parameters
    ----------
    identifier: anonapi.parameters.SourceIdentifier
        The identifier for which to get the id input

    Returns
    -------
    str
        Value to pass as source_instance_id to IDIS api server
    """
    if type(identifier) == StudyInstanceUIDIdentifier:
        return str(identifier.identifier)
    else:
        return str(identifier)  # will prepend the identifier type


COMMON_JOB_PARAMETERS = [SourceIdentifierParameter, PseudoID, PseudoName, Description]
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
