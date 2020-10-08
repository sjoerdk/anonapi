"""Settings used by anon console app"""
from io import FileIO
from typing import Dict, List, Optional

import yaml

from anonapi.exceptions import AnonAPIException
from anonapi.objects import RemoteAnonServer
from anonapi.parameters import (
    DestinationPath,
    Parameter,
    ParameterFactory,
    ParameterSet,
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

    def get_active_server_key(self) -> Optional[str]:
        if self.active_server:
            return self.active_server.name
        else:
            return None

    def to_dict(self) -> dict:
        """Dictionary representation of this class. For serialization"""
        return {
            "servers": {x.name: x.url for x in self.servers},
            "active_server_name": self.get_active_server_key(),
            "user_name": self.user_name,
            "user_token": self.user_token,
            "validate_ssl": self.validate_ssl,
            "job_default_parameters": [
                x.to_string() for x in self.job_default_parameters
            ],
        }

    @classmethod
    def from_dict(cls, dict_in: Dict) -> "AnonClientSettings":
        """Build a AnonClientSettings instance from dict, handle
        missing values by substituting defaults
        """
        # Baseline is all defaults
        dict_full = DefaultAnonClientSettings().to_dict()
        # Overwrite defaults with any keys given in input
        dict_full.update(dict_in)

        settings = cls(
            servers=[
                RemoteAnonServer(name, url)
                for name, url in dict_full["servers"].items()
            ],
            user_name=dict_full["user_name"],
            user_token=dict_full["user_token"],
            validate_ssl=dict_full["validate_ssl"],
            job_default_parameters=cls.extract_default_parameters(dict_full),
        )

        settings.active_server = cls.determine_active_server(
            settings=settings, active_server_name=dict_full["active_server_name"]
        )
        return settings

    @classmethod
    def extract_default_parameters(cls, dict_full) -> List[Parameter]:
        """Read default parameters from dict and pad with defaults where needed"""
        # There are three sources for default parameters
        baseline = DefaultAnonClientSettings().job_default_parameters
        from_input = [
            ParameterFactory.parse_from_string(x)
            for x in dict_full["job_default_parameters"]
        ]
        from_input_legacy = cls.extract_legacy_job_default_parameters(dict_full)

        # take results from input and pad out with defaults where needed
        return ParameterSet(
            parameters=from_input + from_input_legacy, default_parameters=baseline
        ).parameters

    @staticmethod
    def extract_legacy_job_default_parameters(dict_in) -> List[Parameter]:
        """Extract job default parameters as they were written before version 1.4
        This makes sure older settings can still be read
        """

        try:
            legacy_defaults = dict_in["create_job_defaults"]
        except KeyError:
            return []
        parameters = []
        if "project_name" in legacy_defaults:
            parameters.append(Project(value=legacy_defaults["project_name"]))
        if "destination_path" in legacy_defaults:
            parameters.append(
                DestinationPath(value=legacy_defaults["destination_path"])
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


class DefaultAnonClientSettings(AnonClientSettings):
    """A settings object with some default values. For testing and for writing
    settings when none are available
    """

    def __init__(self):
        """Create default settings object:

        >>> servers = [RemoteAnonServer("test", "https://hostname_of_api")]
        >>> user_name='username'
        >>> user_token='12345abc'

        """
        super().__init__(
            servers=[RemoteAnonServer("testserver", "https://hostname_of_api")],
            user_name="username",
            user_token="token",
            job_default_parameters=[
                Project(value="NOT_SET"),
                DestinationPath(value=""),
            ],
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
        )

        self.active_server = settings.active_server

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
