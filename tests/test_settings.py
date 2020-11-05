"""Tests for `anonapi.settings` module."""
from io import StringIO
from distutils import dir_util
from pathlib import Path

import pytest

from anonapi.cli import entrypoint
from anonapi.exceptions import AnonAPIException
from anonapi.parameters import Project
from anonapi.settings import (
    AnonClientSettingsException,
    AnonClientSettings,
    DefaultAnonClientSettings,
    AnonClientSettingsFromFile,
)
from tests import RESOURCE_PATH


@pytest.fixture
def test_settings_folder(tmp_path):
    """A one-time copy of a folder containing some settings files

    Returns
    -------
    str
        root_path to folder

    """
    template_folder = Path(RESOURCE_PATH) / "test_settings"
    dir_util.copy_tree(str(template_folder), str(tmp_path))
    return tmp_path


@pytest.fixture
def test_settings_file(test_settings_folder):
    """Copy of a correctly formatted settings file"""
    return test_settings_folder / "settings.yml"


def assert_test_settings_file_contents(settings: AnonClientSettings):
    """Asserts that the given settings do indeed contain the contents expected from
    test_settings/settings.yml

    Used in several contexts, hence a separate method
    """
    assert settings.user_name == "kees"
    assert settings.user_token == "token"
    assert settings.active_server.name == "sandbox"
    assert type(settings.job_default_parameters[0]) == Project
    assert settings.job_default_parameters[0].value == "Wetenschap-Algemeen"
    assert len(settings.servers) == 2


def test_settings_load(test_settings_folder):
    settings = AnonClientSettingsFromFile(test_settings_folder / "settings.yml")
    assert_test_settings_file_contents(settings)


def test_settings_load_active_mapping_none(tmp_path):
    """A common situation for newly installed anonapi recreates #282"""
    settings_path = tmp_path / "test_settings.yaml"
    DefaultAnonClientSettings(active_mapping_file=None).save_to_file(settings_path)
    settings = AnonClientSettingsFromFile(settings_path)
    assert settings.active_mapping_file is None


def test_settings_from_file(test_settings_folder):
    # load settings
    settings = AnonClientSettingsFromFile(path=test_settings_folder / "settings.yml")
    assert len(settings.servers) == 2

    # make a change and save
    sandbox, p01 = settings.servers
    assert settings.active_server.name == sandbox.name
    settings.active_server = p01
    settings.save()

    # was the change saved?
    loaded = AnonClientSettingsFromFile(path=test_settings_folder / "settings.yml")
    assert loaded.active_server.name == p01.name

    # can these settings still be save to any stream?
    file = StringIO()
    loaded.save_to(file)
    file.seek(0)
    loaded_again = AnonClientSettings.load_from(file)
    assert loaded.user_name == loaded_again.user_name


def test_settings_save(test_settings_folder):
    """Load settings, change, save and see whether they have been saved"""
    settings = AnonClientSettingsFromFile(test_settings_folder / "settings.yml")
    assert settings.user_name == "kees"

    settings.user_name = "other_username"
    settings.save()

    # load settings again to rule out any data being persisted in object
    new_settings = AnonClientSettingsFromFile(test_settings_folder / "settings.yml")
    assert new_settings.user_name == "other_username"


def test_settings_save_with_none_active(test_settings_folder):
    """Fixing a bug found live: saving when active server = none"""
    settings = AnonClientSettingsFromFile(test_settings_folder / "settings.yml")

    # It is possible that there is no active server. You should still be able to save
    settings.active_server = None
    settings.save()

    # And also load
    with open(test_settings_folder / "settings.yml", "r") as f:
        new_settings = AnonClientSettings.load_from(f)
    assert new_settings.active_server is None


@pytest.mark.parametrize(
    "faulty_setting_file", ["settings_wrong.yml", "settings_wrong_2.yml"]
)
def test_settings_load_error(test_settings_folder, faulty_setting_file):
    """Poor man's YAML validation should at least raise some informative exception
    when a key is missing from settings
    """
    with pytest.raises(AnonClientSettingsException):
        AnonClientSettingsFromFile(test_settings_folder / faulty_setting_file)


def test_anon_client_settings_init_with_no_servers():
    # this should not crash
    AnonClientSettings(servers=[], user_name="test", user_token="token")
    DefaultAnonClientSettings()


def test_settings_load_old(test_settings_folder):
    """A parameter was added to settings. You should still be able to load older
    settings files that do not contain this settings. A default version of the new
    setting should be added silently
    """
    settings = AnonClientSettingsFromFile(test_settings_folder / "settings_old.yml")

    assert settings.user_name == "kees"
    assert settings.user_token == "token"
    assert settings.active_server.name == "sandbox"
    assert settings.job_default_parameters is not None
    assert len(settings.servers) == 2


def test_settings_edit(mock_main_runner, test_settings_folder):
    mock_main_runner.invoke(entrypoint.cli, ["settings", "edit"])


def test_load_v1_4_settings_conversion(test_settings_folder):
    """At v1.4.0 settings format changed. Make sure older format settings
    files can still be read, but are then saved in the new format
    """
    # Read an pre-1.4-style settings file
    settings = AnonClientSettingsFromFile(test_settings_folder / "settings.yml")
    assert_test_settings_file_contents(settings)

    # Save it and then load again
    file = StringIO()
    settings.save_to(file)

    # sanity check: This has now been written as post-1.4-style
    file.seek(0)
    assert "- project,Wetenschap-Algemeen" in file.read()
    file.seek(0)

    # and the content should not have been altered
    assert_test_settings_file_contents(AnonClientSettings.load_from(file))


def test_load_v1_4_settings(test_settings_folder):
    """After v1.3.1 settings format changed. Make pre and post 1_4 settings
    can both be read
    """
    # post-change should be loadable
    assert_test_settings_file_contents(
        AnonClientSettingsFromFile(test_settings_folder / "settings_post_1_4_style.yml")
    )

    # pre-change should be loadable
    assert_test_settings_file_contents(
        AnonClientSettingsFromFile(test_settings_folder / "settings.yml")
    )


def test_load_garbage():
    """Loading complete garbage should yield normal exception"""
    with pytest.raises(AnonAPIException):
        AnonClientSettings.load_from(
            StringIO("Not a dictionary\n probably yaml though")
        )
    with pytest.raises(AnonAPIException):
        AnonClientSettings.load_from("just a string??")


def test_load_v1_4_settings_alternate(test_settings_folder):
    """Recreates live exception"""
    AnonClientSettingsFromFile(
        test_settings_folder / "settings_pre_1_4_alternate.yml"
    )  # should just not crash


def test_settings_save_load_active_mapping(test_settings_folder):
    """Recreates error saving Path objects in settings

    Did not realise that YAML saves Path instances as weird full lists. Probably
    the most universal, but I want the settings file to be human readable in that
    does not do it. Casting Path to string for serialization now
    """
    settings = AnonClientSettingsFromFile(test_settings_folder / "settings.yml")
    path = Path("/some/path/settingsfile")
    settings.active_mapping_file = path
    settings.save()
    loaded = AnonClientSettingsFromFile(test_settings_folder / "settings.yml")
    assert loaded.active_mapping_file == path
