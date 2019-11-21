"""Click group and commands for the 'select' subcommand
"""
import os
from pathlib import Path

import click

from anonapi.cli.parser import command_group_function, AnonCommandLineParser, echo_error
from anonapi.selection import DICOMFileFolder, DICOMFileList
from fileselection.fileselection import FileSelectionFolder, FileSelectionFile
from tqdm import tqdm


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


def describe_selection(selection):
    """Create a human readable description of the given selection

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
def main(ctx):
    """select files for a single anonymization job"""
    parser: AnonCommandLineParser = ctx.obj
    context = SelectCommandContext(current_path=parser.current_dir())
    ctx.obj = context


@command_group_function()
def status(context: SelectCommandContext):
    """Show selection in current directory"""
    try:
        selection = context.get_current_selection()
        click.echo(describe_selection(selection))
    except FileNotFoundError as e:
        echo_error(CLIMessages.NO_SELECTION_DEFINED)


@command_group_function()
def delete(context: SelectCommandContext):
    """Show selection in current directory"""

    selection_folder = context.get_current_selection_folder()
    if selection_folder.has_file_selection():
        os.remove(selection_folder.get_data_file_path())
        click.echo("Removed file selection in current folder")
    else:
        echo_error(CLIMessages.NO_SELECTION_DEFINED)


@command_group_function()
def create(context: SelectCommandContext):
    """Recursively find all DICOM files in this dirfor the current directory,
    add all DICOM files"""

    selection_folder = context.get_current_selection_folder()
    if selection_folder.has_file_selection():
        echo_error("There is already a selection in this folder")
    else:
        click.echo("Creating selection in current folder. Adding all DICOM files")
        create_dicom_selection_click(context.current_path)


@command_group_function()
@click.argument("pattern", type=str)
@click.option("--recurse/--no-recurse", default=True, help="Recurse into directories")
@click.option(
    "--check-dicom/--no-check-dicom",
    default=False,
    help="Allows only DICOM files. Opens all files",
)
def add(context: SelectCommandContext, pattern, recurse, check_dicom):
    """Add all files matching given pattern to the selection in the current folder
    """
    selection_folder = context.get_current_selection_folder()
    if selection_folder.has_file_selection():
        echo_error("There is already a selection in this folder")
        return

    if recurse:
        click.echo(f"Finding all files matching '{pattern}' recursively")
        glob_pattern = f"**/{pattern}"
    else:
        click.echo(f"Finding all files matching '{pattern}'")
        glob_pattern = f"{pattern}"

    all_paths = [
        x for x in tqdm(context.current_path.glob(glob_pattern)) if x.is_file()
    ]

    if check_dicom:
        click.echo("Checking that each file is Dicom")
        to_add = [x[0] for x in tqdm(DICOMFileList(all_paths)) if x[1] is not None]
    else:
        to_add = all_paths

    click.echo(f"added {len(to_add)}")



@command_group_function()
def edit(context: SelectCommandContext):
    """initialise a selection for the current directory, add all DICOM files"""

    selection_folder = context.get_current_selection_folder()
    if not selection_folder.has_file_selection():
        echo_error(CLIMessages.NO_SELECTION_DEFINED)
    else:
        click.launch(str(selection_folder.get_data_file_path()))



# TODO: replace this function
def create_dicom_selection_click(path):
    """Find all DICOM files path (recursive) and save them a FileSelectionFile.

    Meant to be included directly inside click commands. Uses a lot of click.echo()

    Parameters
    ----------
    path: PathLike
    """
    # Find all dicom files in this folder
    click.echo(f"Adding '{path}' to mapping")
    folder = DICOMFileFolder(path)
    click.echo(f"Finding all files in {path}")
    files = [x for x in tqdm(folder.all_files()) if x is not None]
    click.echo(f"Found {len(files)} files. Finding out which ones are DICOM")
    dicom_files = [
        x[0] for x in tqdm(folder.all_dicom_files(files)) if x[1] is not None
    ]
    click.echo(f"Found {len(dicom_files)} DICOM files")
    # record dicom files as fileselection
    selection_folder = FileSelectionFolder(path=path)
    selection = FileSelectionFile(
        data_file_path=selection_folder.get_data_file_path(),
        description=Path(path).name + " auto-generated by anonapi",
        selected_paths=dicom_files,
    )
    selection_folder.save_file_selection(selection)


for func in [status, delete, create, edit, add]:
    main.add_command(func)
