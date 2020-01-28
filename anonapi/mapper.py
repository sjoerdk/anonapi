"""Makes it possible to map source files to anonymized id, name etc.
Pre-processing step for creating IDIS jobs

Meant to be usable in a command line, with minimal windows editing tools. Maybe
Excel, maybe notepad

"""
import csv
import os

from anonapi.exceptions import AnonAPIException
from anonapi.parameters import PatientID, PatientName, Description, PIMSKey, \
    DestinationPath, FileSelectionFolderIdentifier, FileSelectionIdentifier, \
    StudyInstanceUIDIdentifier, AccessionNumberIdentifier, SourceIdentifierFactory, \
    SourceIdentifierParameter, ParameterFactory
from collections import UserDict, defaultdict
from io import StringIO
from pathlib import Path
from os import path


class AnonymizationParameters:
    """Settings that can be set when creating a job

    Collecting these together in an object why again?

    """
    # parameter classes
    PATIENT_ID = PatientID
    PATIENT_NAME = PatientName
    DESCRIPTION = Description
    PIMS_KEY = PIMSKey
    DESTINATION_PATH = DestinationPath

    parameters = [PATIENT_ID, PATIENT_NAME, DESCRIPTION, PIMS_KEY, DESTINATION_PATH]
    field_names = [x.field_name for x in parameters]

    def __init__(
        self, patient_id=None, patient_name=None, description=None, pims_key=None,
            output_path=None, destination_path=None
    ):
        self.patient_id = patient_id
        self.patient_name = patient_name
        self.description = description
        self.pims_key = pims_key
        self.destination_path = destination_path

    def as_parameters(self):
        """This object as a list of instantiated Parameter objects.

        Returns
        -------
        List[Parameter]
        """
        return [self.PATIENT_ID(self.patient_id),
                self.PATIENT_NAME(self.patient_name),
                self.DESCRIPTION(self.description),
                self.PIMS_KEY(self.pims_key),
                self.DESTINATION_PATH(self.destination_path)]


    def as_dict(self, parameters_to_include=None):
        """

        Parameters
        ----------
        parameters_to_include: List[Parameter], optional
            List of Parameter objects to write. Defaults
            to all parameters

        Returns
        -------

        """
        params = self.as_parameters()
        if parameters_to_include:
            params = [x for x in params if type(x) in parameters_to_include]
        as_dict = {}

        for param in params:
            value = param.value
            if not value:
                value = ""
            as_dict[param.field_name] = value

        return as_dict

        return params


class Mapping:
    """Everything needed for creating anonymization jobs

    Wrapper around MappingList that adds description and mapping-wide settings
    such as output dir
    """

    # Headers used in between sections in csv file
    DESCRIPTION_HEADER = "## Description ##"
    OPTIONS_HEADER = "## Options ##"
    MAPPING_HEADER = "## Mapping ##"
    ALL_HEADERS = [DESCRIPTION_HEADER, OPTIONS_HEADER, MAPPING_HEADER]

    def __init__(self, mapping, options, description=None):
        """

        Parameters
        ----------
        mapping: MappingList
            The per-job mapping table
        options: List[Parameter]
            List of parameters that have been set for the entire mapping
        description: str, optional
            Human readable description of this mapping. Can contain newline chars
        """
        self.mapping = mapping
        self.options = options
        self.description = description

    def save(self, f):
        # write description
        f.write(self.DESCRIPTION_HEADER + os.linesep)
        f.write(self.description)
        f.write(os.linesep)

        # write options
        f.write(self.OPTIONS_HEADER + os.linesep)
        f.write(os.linesep.join([str(x) for x in self.options]))
        f.write(os.linesep)
        f.write(os.linesep)

        # write mapping
        f.write(self.MAPPING_HEADER + os.linesep)
        mapping_content = StringIO()
        self.mapping.save(mapping_content)
        mapping_content.seek(0)
        f.write(mapping_content.read())

    @classmethod
    def load(cls, f):
        """ Load a mapping from a csv file stream """
        # split content into three sections

        sections = cls.parse_sections(f)

        description = "".join([x for x in sections[cls.DESCRIPTION_HEADER]
                               if x is not '\n' and x is not '\r\n'])

        option_lines = [x.replace('\r', '').replace('\n', '') for x in
                        sections[cls.OPTIONS_HEADER]]
        option_lines = [x for x in option_lines if x]  # remove empty lines
        options = [ParameterFactory.parse_from_string(line) for line in option_lines]

        mapping_content = StringIO("".join(sections[cls.MAPPING_HEADER]))
        mapping = MappingList.load(mapping_content)
        return cls(mapping=mapping,
                   options=options,
                   description=description)

    @classmethod
    def parse_sections(cls, f):
        """A mapping csv file consists of three sections devided by headers.
         Try to parse each one

        Parameters
        ----------
        f: file handled opened with read flag

        Returns
        -------
        Dict
            A dict with all lines under each of the headers in cls.ALL_HEADERS

        Raises
        ------
        MappingLoadError
            If not all headers can be found or are not in the expected order

        """
        collected = defaultdict(list)
        headers_to_find = cls.ALL_HEADERS.copy()
        header_to_find = headers_to_find.pop(0)
        current_header = None
        for line in f.readlines():
            if header_to_find.lower() in line.lower():
                # this is our header, start recording
                current_header = header_to_find
                # and look for the next one. If there is one.
                if headers_to_find:
                    header_to_find = headers_to_find.pop(0)
                continue  # skip header line itself
            if current_header:
                collected[current_header].append(line)

        # check the results do we have all headers?
        if headers_to_find:
            raise MappingLoadError(
                f'Could not find required headers "{headers_to_find}"')

        return collected


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

    def save(self, f, parameters_to_write=AnonymizationParameters.parameters):
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
            fieldnames=[x.field_name for x in ([SourceIdentifierParameter] + parameters_to_write)],
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

    def save_list(self, mapping_list):
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


class MapperException(AnonAPIException):
    pass


class MappingLoadError(MapperException):
    pass
