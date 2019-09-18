"""Conftest.py is loaded for each pytest. Contains fixtures shared by multiple tests, amongs other things """
import shutil
from pathlib import Path

from _pytest.fixtures import fixture
from click.testing import CliRunner
from fileselection.fileselection import FileSelectionFolder

from anonapi.cli.parser import AnonCommandLineParser
from anonapi.client import WebAPIClient, AnonClientTool
from anonapi.mapper import MappingListFolder, ExampleMappingList
from anonapi.objects import RemoteAnonServer
from anonapi.settings import DefaultAnonClientSettings
from tests.factories import RequestsMock
from tests import RESOURCE_PATH


@fixture
def mock_requests(monkeypatch):
    """Make sure anonapi.client does not do any actuall http calls. Also makes it possible to set http responses

    Returns
    -------
    RequestsMock
    """
    requests_mock = RequestsMock()
    monkeypatch.setattr("anonapi.client.requests", requests_mock.requests)
    return requests_mock


@fixture
def mocked_requests_client():
    """A WebAPIClient instance that does not actually do http calls but uses mocked responses

    Returns
    -------
    (WebAPIClient, RequestsMock)
        client with mocked requests lib, and te mocked requests lib itself

    """
    client = WebAPIClient(hostname="test.host", username="testuser", token="token")

    requests_mock = RequestsMock()
    client.requestslib = requests_mock
    return client, requests_mock


@fixture
def anonapi_mock_cli(monkeypatch, tmpdir):
    """Returns AnonCommandLineParser object and sets this as the default object passed to all click invocations of
     entrypoint.cli with empty current dir

    """
    settings = DefaultAnonClientSettings()
    settings.servers.append(RemoteAnonServer("testserver2", "https://hostname_of_api2"))
    tool = AnonClientTool(username=settings.user_name, token=settings.user_token)
    mock_parser = AnonCommandLineParser(client_tool=tool, settings=settings)
    mock_parser.current_dir = lambda: str(tmpdir)
    monkeypatch.setattr("anonapi.cli.entrypoint.get_parser", lambda: mock_parser)

    return mock_parser


@fixture
def a_folder_with_mapping(tmpdir):
    shutil.copyfile(
        RESOURCE_PATH / "test_cli" / "anon_mapping.csv",
        Path(tmpdir) / "anon_mapping.csv",
    )
    return tmpdir


@fixture
def a_folder_with_mapping_diverse(tmpdir):
    """In addition to a_folder_with_mapping, contains also pacskey identifiers. (Added these later)"""
    shutil.copyfile(
        RESOURCE_PATH / "test_cli" / "anon_mapping_diverse.csv",
        Path(tmpdir) / "anon_mapping.csv",
    )
    return tmpdir


@fixture
def anon_mock_cli_with_mapping(anonapi_mock_cli, a_folder_with_mapping):
    anonapi_mock_cli.current_dir = lambda: str(a_folder_with_mapping)
    return anonapi_mock_cli


@fixture
def folder_with_some_dicom_files(tmpdir):
    """A folder with some structure, some dicom files and some non-dicom files. No FileSelectionFile saved yet"""
    a_folder = tmpdir / "a_folder"
    shutil.copytree(RESOURCE_PATH / "test_cli" / "test_dir", a_folder)
    return FileSelectionFolder(path=a_folder)


class MockContextCliRunner(CliRunner):
    """a click.testing.CliRunner that always passes a mocked context to any call, making sure any operations
    on current dir are done in a temp folder"""

    def __init__(self, *args, mock_context, **kwargs):

        super().__init__(*args, **kwargs)
        self.mock_context = mock_context

    def invoke(
        self,
        cli,
        args=None,
        input=None,
        env=None,
        catch_exceptions=True,
        color=False,
        mix_stderr=False,
        **extra
    ):
        return super().invoke(
            cli,
            args,
            input,
            env,
            catch_exceptions,
            color,
            mix_stderr,
            obj=self.mock_context,
        )


class AnonCommandLineParserRunner(MockContextCliRunner):
    """A click runner that always injects a AnonCommandLineParser instance into the context
    """

    def __init__(self, *args, mock_context, **kwargs):
        """

        Parameters
        ----------
        mock_context: AnonCommandLineParser
        """
        super().__init__(*args, mock_context=mock_context, **kwargs)

    def set_mock_current_dir(self, path):
        """Any anonapi operations called will use this is as current directory

        Parameters
        ----------
        path: PathLike
        """
        self.mock_context.current_dir = lambda: path

    def get_parser(self):
        """Get the parser instance that is injected by this runner

        Returns
        -------
        AnonCommandLineParser
        """
        return self.mock_context
