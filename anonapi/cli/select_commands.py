"""Click group and commands for the 'select' subcommand"""
import os

import click
from click.exceptions import ClickException

from anonapi.decorators import pass_anonapi_context
from anonapi.logging import get_module_logger
from anonapi.selection import FileFolder, find_dicom_files
from fileselection.fileselection import FileSelectionFolder
from pathlib import Path
from tqdm import tqdm

logger = get_module_logger(__name__)


class CLIMessages:
    NO_SELECTION_DEFINED = "There is no selection defined in current folder"


class SelectCommandContext:
    def __init__(self, current_path):
        self.current_path = Path(current_path)

    def get_current_selection_folder(self):
        return FileSelectionFolder(self.current_path)

    def get_current_selection(self):
        """Load selection in current folder

        Returns
        -------
        FileSelectionFile

        Raises
        ------
        FileNotFoundError
            When there is no selection in current folder

        """

        return self.get_current_selection_folder().load_file_selection()


pass_select_command_context = click.make_pass_decorator(SelectCommandContext)


def describe_selection(selection):
    """Create a human-readable description of the given selection

    Parameters
    ----------
    selection: FileSelectionFile


    Returns
    -------
    str

    """
    return (
        f"Selection containing {len(selection.selected_paths)} files:\n"
        f"Description: {selection.description}"
    )


@click.group(name="select")
@click.pass_context
@pass_anonapi_context
def main(context: SelectCommandContext, ctx):
    """Select files for a single anonymization job"""
    ctx.obj = SelectCommandContext(current_path=context.current_dir)


@click.command()
@pass_select_command_context
def status(context: SelectCommandContext):
    """Show selection in current directory"""
    try:
        selection = context.get_current_selection()
        logger.info(describe_selection(selection))
    except FileNotFoundError as e:
        raise ClickException(CLIMessages.NO_SELECTION_DEFINED) from e


@click.command()
@pass_select_command_context
def delete(context: SelectCommandContext):
    """Remove selection file in current directory"""

    selection_folder = context.get_current_selection_folder()
    if selection_folder.has_file_selection():
        os.remove(selection_folder.get_data_file_path())
        logger.info("Removed file selection in current folder")
    else:
        raise ClickException(CLIMessages.NO_SELECTION_DEFINED)


@click.command()
@pass_select_command_context
@click.argument("pattern", type=str)
@click.option(
    "--recurse/--no-recurse",
    default=True,
    help="Search for files to add in subfolders as well. On by default",
)
@click.option(
    "--check-dicom/--no-check-dicom",
    default=True,
    help="Only add files that are valid DICOM file. For many files, this might "
    "take some time. On by default.",
)
@click.option(
    "--exclude-pattern",
    "-e",
    multiple=True,
    help="Exclude any file matching the given pattern. The pattern can use ``*`` "
    "to match any part of a name. --exclude-pattern can be used "
    "multiple times, to exclude multiple patterns",
)
def add(context: SelectCommandContext, pattern, recurse, check_dicom, exclude_pattern):
    """Add all files matching pattern to selection in the current directory.

    Excludes 'fileselection.txt'
    """
    logger.info(f"Finding files...")
    current_folder = FileFolder(context.current_path)
    paths = list(
        tqdm(
            current_folder.iterate(
                pattern=pattern,
                recurse=recurse,
                exclude_patterns=["fileselection.txt"] + list(exclude_pattern),
            )
        )
    )

    if check_dicom:
        paths = find_dicom_files(paths)

    selection_folder = context.get_current_selection_folder()
    if selection_folder.has_file_selection():
        selection = selection_folder.load_file_selection()
        selection.add(paths)
    else:
        selection = selection_folder.create_file_selection_file(
            description=selection_folder.path.name + " auto-generated by anonapi",
            selected_paths=paths,
        )

    selection.save_to_file()
    logger.info(f"selection now contains {len(selection.selected_paths)} files")


@click.command()
@pass_select_command_context
def edit(context: SelectCommandContext):
    """Open selection file in default editor"""

    selection_folder = context.get_current_selection_folder()
    if not selection_folder.has_file_selection():
        raise ClickException(CLIMessages.NO_SELECTION_DEFINED)
    else:
        click.launch(str(selection_folder.get_data_file_path()))


for func in [status, delete, edit, add]:
    main.add_command(func)
