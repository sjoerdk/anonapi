"""Click group and commands for the 'map' subcommand
"""
from pathlib import Path

import click
import datetime
import random
import string

from fileselection.fileselection import FileSelectionFolder, FileSelectionFile
from tqdm import tqdm

from anonapi.cli.parser import command_group_function, AnonCommandLineParser, MappingLoadException
from anonapi.mapper import get_example_mapping_list, SourceIdentifierFactory, open_mapping_in_editor,\
    MappingListFolder, MappingList, MapperException, AnonymizationParameters
from anonapi.selection import DICOMFileFolder


class MapCommandContext:

    def __init__(self, current_path):
        self.current_path = current_path

    def get_current_mapping_folder(self):
        return MappingListFolder(self.current_path)

    def get_current_mapping(self):
        """Load mapping from the current directory

        Returns
        -------
        MappingList
            Loaded from current dir

        Raises
        ------
        MappingLoadException
            When no mapping could be loaded from current directory

        """

        try:
            with open(self.get_current_mapping_folder().full_path(), 'r') as f:
                return MappingList.load(f)
        except FileNotFoundError:
            raise MappingLoadException('No mapping defined in current directory')
        except MapperException as e:
            raise MappingLoadException(f'Error loading mapping: {e}')


@click.group(name='map')
@click.pass_context
def main(ctx):
    """map original data to anonymized name, id, etc."""
    parser: AnonCommandLineParser = ctx.obj
    context = MapCommandContext(current_path=parser.current_dir())
    ctx.obj = context


@command_group_function()
def status(context: MapCommandContext):
    """Show mapping in current directory"""
    try:
        mapping = context.get_current_mapping()
        click.echo(mapping.to_table_string())
    except MappingLoadException as e:
        click.echo(e)


@command_group_function()
def init(context: MapCommandContext):
    """Save a default mapping in the current folder"""
    folder = context.get_current_mapping_folder()
    mapping_list = get_example_mapping_list()
    folder.save_list(mapping_list)
    click.echo(f"Initialised empty mapping in {mapping_list.DEFAULT_FILENAME}")


@command_group_function()
def delete(context: MapCommandContext):
    """delete mapping in current folder"""
    folder = context.get_current_mapping_folder()
    if not folder.has_mapping_list():
        click.echo("No mapping defined in current folder")
        return
    folder.delete_list()
    click.echo(f"Removed mapping in current dir")


@command_group_function()
@click.argument('path', type=click.Path(exists=True))
def add_study_folder(context: MapCommandContext, path):
    """Add all dicom files in given folder to map
    """
    # check whether there is a mapping
    mapping = context.get_current_mapping()

    # Find all dicom files in this folder
    click.echo(f"Adding '{path}' to mapping")
    folder = DICOMFileFolder(path)
    click.echo(f"Finding all files in {path}")
    files = [x for x in tqdm(folder.all_files()) if x is not None]
    click.echo(f"Found {len(files)} files. Finding out which ones are DICOM")
    dicom_files = [x[0] for x in tqdm(folder.all_dicom_files(files)) if x[1] is not None]
    click.echo(f"Found {len(dicom_files)} DICOM files")

    # record dicom files as fileselection
    selection_folder = FileSelectionFolder(path=path)
    selection = FileSelectionFile(
        data_file_path=selection_folder.get_data_file_path(),
        description=Path(path).name,
        selected_paths=dicom_files
    )
    selection_folder.save_file_selection(selection)

    # add this folder to mapping
    folder_source_id = SourceIdentifierFactory().get_source_identifier(f'folder:{path}')
    patient_name = f"autogenerated_{''.join(random.choices(string.ascii_uppercase + string.digits, k=5))}"
    patient_id = "auto_" + ''.join(map(str, random.choices(range(10), k=8)))
    description = f"auto generated_{datetime.date.today().strftime('%B %d, %Y')}"
    mapping[folder_source_id] = AnonymizationParameters(
                                    patient_name=patient_name,
                                    patient_id=patient_id,
                                    description=description)

    context.get_current_mapping_folder().save_list(mapping)
    click.echo(f"Done. Added '{path}' to mapping")


@command_group_function()
def edit(context: MapCommandContext):
    """Edit the current mapping in editor
    """
    open_mapping_in_editor(context.get_current_mapping_folder().full_path())


for func in [status, init, delete, add_study_folder, edit]:
    main.add_command(func)
