"""Conftest.py is loaded for each pytest. Contains fixtures shared by multiple tests, amongs other things """
import shutil
from pathlib import Path
from unittest.mock import Mock

from _pytest.fixtures import fixture
from click.testing import CliRunner
from fileselection.fileselection import FileSelectionFolder

from anonapi.context import AnonAPIContext
from anonapi.client import WebAPIClient, AnonClientTool
from anonapi.mapper import MappingListFolder, ExampleMappingList
from anonapi.objects import RemoteAnonServer
from anonapi.settings import DefaultAnonClientSettings
from tests.factories import RequestsMock
from tests import RESOURCE_PATH


@fixture
def mock_requests(monkeypatch):
    """Make sure anonapi.client does not do any actuall http calls. Also makes it
     possible to set http responses

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
def a_folder_with_mapping(tmpdir):
    shutil.copyfile(
        RESOURCE_PATH / "test_cli" / "anon_mapping.csv",
        Path(tmpdir) / "anon_mapping.csv",
    )
    return tmpdir


@fixture
def a_folder_with_mapping_and_fileselection(a_folder_with_mapping, a_file_selection):
    target_path = Path(a_folder_with_mapping) / "a_folder" / 'a_file_selection.txt'
    target_path.parent.mkdir(exist_ok=True)
    shutil.copyfile(a_file_selection, target_path)
    return a_folder_with_mapping, target_path


@fixture
def mock_cli_with_mapping(anonapi_mock_cli, a_folder_with_mapping):
    anonapi_mock_cli.current_dir = a_folder_with_mapping
    return anonapi_mock_cli


@fixture
def a_folder_with_mapping_diverse(tmpdir):
    """In addition to a_folder_with_mapping, contains also pacskey identifiers.
     (Added these later)"""
    shutil.copyfile(
        RESOURCE_PATH / "test_cli" / "anon_mapping_diverse.csv",
        Path(tmpdir) / "anon_mapping.csv",
    )
    return tmpdir


@fixture
def folder_with_some_dicom_files(tmpdir):
    """A folder with some structure, some dicom files and some non-dicom files.
    No FileSelectionFile saved yet"""
    a_folder = tmpdir / "a_folder"
    shutil.copytree(RESOURCE_PATH / "test_cli" / "test_dir", a_folder)
    return FileSelectionFolder(path=a_folder)


@fixture
def a_file_selection(tmpdir):
    """A file with a valid file selection """
    return RESOURCE_PATH / "test_cli" / "selection" / "fileselection.txt"


@fixture()
def mock_api_context(tmpdir):
    """Context required by many anonapi commands. Will yield a temp folder as
    current_dir"""
    settings = DefaultAnonClientSettings()
    settings.servers.append(RemoteAnonServer("testserver2",
                                             "https://hostname_of_api2"))
    context = AnonAPIContext(client_tool=AnonClientTool(username='test',
                                                        token='token'),
                             settings=settings,
                             current_dir=Path(tmpdir))
    return context


@fixture()
def mock_cli_base_context(monkeypatch, mock_api_context):
    """entrypoint.cli creates a context from local settings. Stop this and return a
    mock context instead
    """
    monkeypatch.setattr("anonapi.cli.entrypoint.get_context",
                        lambda: mock_api_context)


@fixture()
def mock_main_runner(mock_api_context, mock_cli_base_context):
    """a click.testing.CliRunner that always passes a mocked context to any call,
    making sure any operations on current dir are done in a temp folder"""
    runner = AnonAPIContextRunner(mock_context=mock_api_context)
    return runner


class MockContextCliRunner(CliRunner):
    """a click.testing.CliRunner that always passes a mocked context to any call,
    making sure any operations on current dir are done in a temp folder"""

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


class AnonAPIContextRunner(MockContextCliRunner):
    """A click runner that always injects a AnonAPIContext instance into the context
    """

    def __init__(self, *args, mock_context, **kwargs):
        """

        Parameters
        ----------
        mock_context: AnonAPIContext
        """
        super().__init__(*args, mock_context=mock_context, **kwargs)

    def set_mock_current_dir(self, path):
        """Any anonapi operations called will use this is as current directory

        Parameters
        ----------
        path: PathLike
        """
        self.mock_context.current_dir = path

    def get_context(self):
        """Get the context instance that is injected by this runner

        Returns
        -------
        AnonAPIContext
        """
        return self.mock_context
