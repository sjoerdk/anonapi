"""Conftest.py is loaded for each pytest. Contains fixtures shared by multiple tests, amongs other things """
import shutil
from pathlib import Path

from _pytest.fixtures import fixture
from fileselection.fileselection import FileSelectionFolder

from anonapi.cli.parser import AnonClientTool, AnonCommandLineParser
from anonapi.client import WebAPIClient
from anonapi.objects import RemoteAnonServer
from anonapi.settings import AnonClientSettings
from tests.factories import RequestsMock
from tests import RESOURCE_PATH


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
def anonapi_mock_cli(monkeypatch):
    """Returns AnonCommandLineParser object and sets this as the default object passed to all click invocations of
     entrypoint.cli


    """
    settings = AnonClientSettings(
        servers=[
            RemoteAnonServer(name="testserver", url="https://testurl"),
            RemoteAnonServer(name="testserver2", url="https://testurl2"),
        ],
        user_name="testuser",
        user_token="testtoken",
    )
    tool = AnonClientTool(username=settings.user_name, token=settings.user_token)
    mock_parser = AnonCommandLineParser(client_tool=tool, settings=settings)
    monkeypatch.setattr("anonapi.cli.entrypoint.get_parser", lambda: mock_parser)

    return mock_parser


@fixture
def anon_mock_cli_with_mapping(anonapi_mock_cli, tmpdir):
    shutil.copyfile(RESOURCE_PATH / "test_cli" / "anon_mapping.csv", Path(tmpdir) / "anon_mapping.csv")
    anonapi_mock_cli.current_dir = lambda: str(tmpdir)
    return anonapi_mock_cli


@fixture
def folder_with_some_dicom_files(tmpdir):
    """A folder with some structure, some dicom files and some non-dicom files. No FileSelectionFile saved yet"""
    a_folder = tmpdir / "a_folder"
    shutil.copytree(RESOURCE_PATH / "test_cli" / "test_dir", a_folder)
    return FileSelectionFolder(path=a_folder)
