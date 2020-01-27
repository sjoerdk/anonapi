from pytest import fixture

from anonapi.cli.map_commands import MapCommandContext, add_selection
from tests.conftest import MockContextCliRunner


class MapCommandLineParser(MockContextCliRunner):
    """A click CLIRunner that injects a MapCommandContext

    """
    def __init__(self, *args, mock_context, **kwargs):

        super().__init__(*args, **kwargs)
        self.mock_context = mock_context


@fixture
def map_command_runner_empty_dir(tmpdir):
    """A click CLIRunner that MapCommandContext pointing to an empty dir
    """
    return MockContextCliRunner(mock_context=MapCommandContext(current_path=tmpdir))


@fixture
def map_command_runner_mapping_dir(a_folder_with_mapping):
    """A click CLIRunner that MapCommandContext pointing to a dir with some mapping
    """
    return MockContextCliRunner(mock_context=MapCommandContext(
        current_path=a_folder_with_mapping))


def test_cli_map_add_selection(map_command_runner_mapping_dir,
                               a_folder_with_mapping_and_fileselection):
    """Add a file selection to a mapping."""
    mapping_folder, fileselection_path = a_folder_with_mapping_and_fileselection

    runner = map_command_runner_mapping_dir
    result = runner.invoke(add_selection, str(fileselection_path),
                           catch_exceptions=False)
    assert result.exit_code == 0

    mapping = map_command_runner_mapping_dir.mock_context.get_current_mapping()
    assert len(mapping) == 21
    assert "fileselection:a_folder/a_file_selection.txt" in map(str, mapping.keys())
