"""Parameters that are used to create jobs. Some are quite simple, like 'description'
which is just a string. Others are more complex, such as 'source' which has its own
type family and validation.

Put these in separate module because parameters appear in several guises throughout
the job creation process and I want a unified type

"""

from anonapi.exceptions import AnonAPIException
from fileselection.fileselection import FileSelectionFile
from pathlib import Path


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

    @classmethod
    def cast_to_subtype(cls, identifier):
        """Try to figure out which subtype of source identifier this is and return
        object of that type

        Parameters
        ----------
        identifier, str
            Valid source identifier, like 'path:/tmp/'

        Raises
        ------
        UnknownSourceIdentifierException
            When source identifier is not recognized

        """
        return SourceIdentifierFactory().get_source_identifier_for_key(identifier)


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
        UnknownSourceIdentifierException:
            When the key cannot be cast to any known identifier

        Returns
        -------
        Instance of SourceIdentifier or subtype
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
            raise UnknownSourceIdentifierException(msg)

        for id_type in self.types:
            if id_type.key == type_key:
                return id_type(identifier=identifier)

        raise UnknownSourceIdentifierException(
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
        UnknownObjectException:
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
            raise UnknownObjectException(f"Unknown object: {object}. I can't create an"
                                f"identifier for this")

        return object_identifier_class.from_object(object)


class Parameter:
    """A typed, human readable,  persistable key-value pair that means something
    in anonapi

    Made this because the mapping csv file contains parameters in different
    forms. I still want to treat them the same
    """

    value_type = str
    field_name = 'parameter'

    def __init__(self, value=None):
        if not value:
            self.value = None  # parameters can be empty, regardless of the type
        else:
            self.value = self.value_type(value)

    def __str__(self):
        if not self.value:
            value = ""
        else:
            value = self.value
        return f"{self.field_name},{value}"


class PatientID(Parameter):
    field_name = 'patient_id'


class PatientName(Parameter):
    field_name = 'patient_name'


class Description(Parameter):
    field_name = 'description'


class PIMSKey(Parameter):
    field_name = 'pims_key'


class OutputPath(Parameter):
    value_type = Path
    field_name = 'output_path'


class SourceIdentifierParameter(Parameter):
    """Reference to the source of the data"""
    value_type = SourceIdentifier
    field_name = 'source'

    def __init__(self, value):
        self.value = SourceIdentifier.cast_to_subtype(value)


class ParameterException(AnonAPIException):
    pass


class UnknownSourceIdentifierException(ParameterException):
    pass


class UnknownObjectException(ParameterException):
    pass
