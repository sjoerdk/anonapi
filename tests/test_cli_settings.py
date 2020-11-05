import pytest

from anonapi.cli.settings_commands import edit
from anonapi.settings import AnonClientSettingsFromFile, DefaultAnonClientSettings
from tests.conftest import AnonAPIContextRunner


@pytest.fixture
def default_settings_from_disk(tmp_path) -> AnonClientSettingsFromFile:
    """Default generated settings that have been written to disk and read again"""
    settings_path = tmp_path / "test_settings.yaml"
    DefaultAnonClientSettings(active_mapping_file=None).save_to_file(settings_path)
    return AnonClientSettingsFromFile(settings_path)


def test_settings_edit(mock_api_context, default_settings_from_disk, mock_launch):
    mock_api_context.settings = default_settings_from_disk
    runner = AnonAPIContextRunner(mock_context=mock_api_context)
    result = runner.invoke(edit)
    assert result.exit_code == 0

    # Check common mistake of calling click.launch(): using a Path instead of str
    path_launched = mock_launch.call_args[0][0]
    assert type(path_launched) == str
    assert path_launched == str(default_settings_from_disk.path)
