"""Makes it possible to map source files to anonymized id, name etc. Pre-processing step for creating IDIS jobs

Meant to be usable in a command line, with minimal windows editing tools. Maybe Excel, maybe notepad

"""
import csv
from collections import UserDict


class SourceIdentifier:
    """A string representing a place where data is coming from

    """
    key = 'base'

    def __init__(self, identifier):
        self.identifier = identifier

    def __str__(self):
        return f'{self.key}:{self.identifier}'


class FileSelectionIdentifier(SourceIdentifier):
    """A file selection in a specific folder
    """
    key = 'folder'


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
            msg = f"'{key}' is not a valid source. There should be a single colon ':' sign somewhere. " \
                  f"Original error: {e}"
            raise UnknownSourceIdentifier(msg)

        for id_type in self.types:
            if id_type.key == type_key:
                return id_type(identifier=identifier)

        raise UnknownSourceIdentifier(f"Unknown identifier '{key}'. Known identifiers: {[x.key for x in self.types]}")


class AnonymizationParameters:
    """Settings that can be set when creating a job and that are likely to change within a single mapping

    """
    PATIENT_ID_NAME = 'patient_id'
    PATIENT_NAME = 'patient_name'
    DESCRIPTION_NAME = 'description'

    field_names = [PATIENT_ID_NAME,
                   PATIENT_NAME,
                   DESCRIPTION_NAME]

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
                    raise ValueError(f"Unknown parameter '{param}'. Allowed: {AnonymizationParameters.field_names}")

        all_values = {self.PATIENT_ID_NAME: self.patient_id,
                      self.PATIENT_NAME: self.patient_name,
                      self.DESCRIPTION_NAME: self.description}
        if parameters_to_include:
            return {key: value for key, value in all_values.items() if key in parameters_to_include}
        else:
            return all_values


class MappingList(UserDict):
    """List of mappings that can be read from and saved to disk

    """
    def __init__(self, mapping):
        """

        Parameters
        ----------
        mapping: Dict[SourceIdentifier, AnonymizationParameters]
            Initialize mapping with this dics


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

        writer = csv.DictWriter(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL,
                                fieldnames=['source'] + parameters_to_write)
        writer.writeheader()
        for identifier, parameters in self.data.items():
            fields = {'source': str(identifier), **parameters.as_dict(parameters_to_include=parameters_to_write)}
            writer.writerow(fields)

    @classmethod
    def load(cls, f):
        reader = csv.DictReader(f)
        id_factory = SourceIdentifierFactory()
        mapping = {}
        for row in reader:
            try:
                source = id_factory.get_source_identifier(row['source'])
            except KeyError as e:
                raise MappingLoadError(f"Could not find column with header 'source'. This is required.")
            # It might be that not all parameters have been written. Set these to None
            parameters = {'patient_id': row.get(AnonymizationParameters.PATIENT_ID_NAME, None),
                          'patient_name': row.get(AnonymizationParameters.PATIENT_NAME, None),
                          'description': row.get(AnonymizationParameters.DESCRIPTION_NAME, None)}
            mapping[source] = AnonymizationParameters(**parameters)
        return cls(mapping)


class MapperException(Exception):
    pass


class UnknownSourceIdentifier(MapperException):
    pass


class MappingLoadError(MapperException):
    pass
