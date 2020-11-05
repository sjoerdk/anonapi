"""Settings used by anon console app"""
from io import FileIO
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from anonapi.exceptions import AnonAPIException
from anonapi.objects import RemoteAnonServer
from anonapi.parameters import (
    DestinationPath,
    Parameter,
    ParameterFactory,
    ParameterParsingError,
    Project,
)
from anonapi.persistence import YAMLSerializable


class AnonClientSettings(YAMLSerializable):
    """Settings used by anonymization web API client"""

    def __init__(
        self,
        servers: List[RemoteAnonServer],
        user_name: str,
        user_token: str,
        job_default_parameters: Optional[List[Parameter]] = None,
        validate_ssl=True,
        active_mapping_file: Optional[Path] = None,
    ):
        """
        Parameters
        ----------
        servers: List[RemoteAnonServer]
            all servers
        user_name: str
            user name
        user_token: str
            API token
        job_default_parameters: Optional[List[Parameter]]
            When creating jobs, use these settings by default. Defaults to empty list
        validate_ssl: bool, optional
            If False, ignore ssl warnings and outdated certificates.
            Defaults to True
        active_mapping_file: Optional[Path]
            Full path to the mapping that is currently being worked on, if any.
            Defaults to None
        """
        self.servers = servers
        try:
            self.active_server = self.servers[0]
        except IndexError:
            self.active_server = None
        self.user_name = user_name
        self.user_token = user_token
        if job_default_parameters is None:
            job_default_parameters = []
        self.job_default_parameters = job_default_parameters
        self.validate_ssl = validate_ssl
        self.active_mapping_file = active_mapping_file

    def get_active_server_key(self) -> Optional[str]:
        if self.active_server:
            return self.active_server.name
        else:
            return None

    def to_dict(self) -> dict:
        """Dictionary representation of this class. For serialization"""
        if self.active_mapping_file is None:
            active_mapping_file = None
        else:
            active_mapping_file = str(self.active_mapping_file)
        return {
            "servers": {x.name: x.url for x in self.servers},
            "active_server_name": self.get_active_server_key(),
            "user_name": self.user_name,
            "user_token": self.user_token,
            "validate_ssl": self.validate_ssl,
            "job_default_parameters": [
                x.to_string() for x in self.job_default_parameters
            ],
            "active_mapping_file": active_mapping_file,
        }

    @classmethod
    def from_dict(cls, dict_in: Dict) -> "AnonClientSettings":
        """Build a AnonClientSettings instance from dict, handle
        missing values by substituting defaults

        Raises
        ------
        ValueError
            If a settings object cannot be created from dict_in
        """
        # Baseline is all defaults
        dict_full = DefaultAnonClientSettings().to_dict()
        # Overwrite defaults with any keys given in input
        dict_full.update(dict_in)

        if dict_full["active_mapping_file"]:
            active_mapping_file = Path(dict_full["active_mapping_file"])
        else:
            active_mapping_file = None

        settings = cls(
            servers=[
                RemoteAnonServer(name, url)
                for name, url in dict_full["servers"].items()
            ],
            user_name=dict_full["user_name"],
            user_token=dict_full["user_token"],
            validate_ssl=dict_full["validate_ssl"],
            job_default_parameters=cls.extract_default_parameters(dict_in),
            active_mapping_file=active_mapping_file,
        )

        settings.active_server = cls.determine_active_server(
            settings=settings, active_server_name=dict_full["active_server_name"]
        )
        return settings

    @classmethod
    def extract_default_parameters(cls, dict_in: Dict) -> List[Parameter]:
        """Default job parameters can be in pre- or post-1.4 format and under one
         of two keys. Try all 4 combinations

        Parameters
        ----------
        dict_in: Dict
            All settings
        """
        # info is in one of these keys:
        keys = [
            key
            for key, value in dict_in.items()
            if key in ["create_job_defaults", "job_default_parameters"]
        ]
        for key in keys:
            try:
                # parse as post-1.4 style
                return [ParameterFactory.parse_from_string(x) for x in dict_in[key]]
            except ParameterParsingError:
                # this did not work. Try old, pre-1.4 style
                return cls.extract_legacy_job_default_parameters(dict_in[key])

    @staticmethod
    def extract_legacy_job_default_parameters(
        job_default_parameters: Dict,
    ) -> List[Parameter]:
        """Extract job default parameters as they were written before version 1.4
        This makes sure older settings can still be read

        Parameters
        ----------
        job_default_parameters: Dict
            The contents of the job default parameters item in settings

        """

        parameters = []
        if "project_name" in job_default_parameters:
            parameters.append(Project(value=job_default_parameters["project_name"]))
        if "destination_path" in job_default_parameters:
            parameters.append(
                DestinationPath(value=job_default_parameters["destination_path"])
            )

        return parameters

    @staticmethod
    def determine_active_server(
        settings: "AnonClientSettings", active_server_name: Optional[str]
    ) -> Optional[RemoteAnonServer]:

        if active_server_name is None:
            return None
        else:
            servers = {x.name: x for x in settings.servers}
            try:
                return servers[active_server_name]
            except KeyError:
                msg = (
                    f"Active server name '{active_server_name}' was not found in "
                    f"list of servers_parsed "
                    f"'{list(servers.keys())}'. I don't know what the active "
                    f"server is supposed to be"
                )
                raise AnonClientSettingsException(msg)

    def as_human_readable(self) -> str:
        return yaml.dump(self.to_dict(), default_flow_style=False)

    def save_to_file(self, filename):
        """Putting save to file method here in base class so I can write settings
        files generated from code
        """
        with open(filename, "w") as f:
            self.save_to(f)

    def save(self):
        """Dummy method to be able to call save() when testing with memory-only
        settings
        """
        raise Warning(
            "Settings not saved. " "There is no file associated with these settings"
        )


class DefaultAnonClientSettings(AnonClientSettings):
    """A settings object with some default values

    Differs from its base class AnonClientSettings in that it will have dummy
    values instead of only empty values when initialised without parameters
    """

    def __init__(self, active_mapping_file: Optional[Path] = None):
        """Settings object with minimal default values. Should be valid as default
         settings object.

        >>> servers = [RemoteAnonServer("test", "https://hostname_of_api")]
        >>> user_name='username'
        >>> user_token='token'

        """
        super().__init__(
            servers=[RemoteAnonServer("testserver", "https://hostname_of_api")],
            user_name="username",
            user_token="token",
            job_default_parameters=[
                Project(value="NOT_SET"),
                DestinationPath(value=""),
            ],
            active_mapping_file=active_mapping_file,
        )


class AnonClientSettingsFromFile(AnonClientSettings):
    """Settings read from a file. Holds on to file path so you can do

    >>> settings = AnonClientSettingsFromFile('/path/to/file')
    >>> settings.save_to()

    Without having to remember the file path yourself and doing open()
    """

    def __init__(self, path: str):
        self.path = path
        # read settings file and set all
        with open(self.path, "r") as f:
            settings: AnonClientSettings = AnonClientSettings.load_from(f)
        super().__init__(
            servers=settings.servers,
            user_name=settings.user_name,
            user_token=settings.user_token,
            job_default_parameters=settings.job_default_parameters,
            validate_ssl=settings.validate_ssl,
            active_mapping_file=settings.active_mapping_file,
        )

        self.active_server = settings.active_server

    def __str__(self):
        return f"AnonClientSettingsFromFile at {self.path}"

    def save(self):
        with open(self.path, "w") as f:
            self.save_to(f)

    @classmethod
    def load_from(cls, f: FileIO):
        raise NotImplementedError("This class can only be loaded from a file")


class AnonClientSettingsException(AnonAPIException):
    pass


class AnonClientSettingsFromFileException(AnonClientSettingsException):
    pass
