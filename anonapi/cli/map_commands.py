"""Click group and commands for the 'map' subcommand
"""
from pathlib import Path
from typing import List, Optional

import click
import datetime
import getpass
import random
import string

from click.exceptions import BadParameter, ClickException

from anonapi.cli.click_types import FileSelectionFileParam
from anonapi.cli.select_commands import create_dicom_selection_click
from anonapi.context import AnonAPIContext
from anonapi.decorators import pass_anonapi_context, handle_anonapi_exceptions
from anonapi.mapper import (
    MappingFolder,
    ExampleJobParameterGrid,
    MapperException,
    Mapping,
)
from anonapi.parameters import (
    SourceIdentifierFactory,
    DestinationPath,
    PatientName,
    SourceIdentifierParameter,
    PatientID,
    Description,
    RootSourcePath,
    Project,
    Parameter,
    FileSelectionIdentifier,
)
from anonapi.settings import AnonClientSettings


class MapCommandContext:
    def __init__(self, current_path, settings: AnonClientSettings):
        self.current_path = current_path
        self.settings = settings

    def get_current_mapping_folder(self):
        return MappingFolder(self.current_path)

    def get_current_mapping(self):
        """Load mapping from the current directory

        Returns
        -------
        Mapping
            Loaded from current dir

        Raises
        ------
        MappingLoadException
            When no mapping could be loaded from current directory

        """
        return self.get_current_mapping_folder().get_mapping()


pass_map_command_context = click.make_pass_decorator(MapCommandContext)


@click.group(name="map")
@click.pass_context
@pass_anonapi_context
def main(context: AnonAPIContext, ctx):
    """map original data to anonymized name, id, etc."""

    # both anonapi_context and base click ctx are passed to be able change ctx.obj
    ctx.obj = MapCommandContext(
        current_path=context.current_dir, settings=context.settings
    )


@click.command()
@handle_anonapi_exceptions
@pass_map_command_context
def status(context: MapCommandContext):
    """Show mapping in current directory"""

    mapping = context.get_current_mapping()
    click.echo(mapping.to_string())


def get_initial_options(settings: AnonClientSettings) -> List[Parameter]:
    """Do the awkward determination of what initially to write in the options
    section of a new mapping """
    defaults = settings.job_default_parameters

    default_project = "Wetenschap-Algemeen"
    default_destination = r"\\server\share\folder"
    if defaults:
        if defaults.project_name:
            default_project = defaults.project_name
        if defaults.destination_path:
            default_destination = defaults.destination_path

    return [Project(default_project), DestinationPath(default_destination)]


@click.command()
@pass_map_command_context
def init(context: MapCommandContext):
    """Save a default mapping in the current folder"""
    folder = context.get_current_mapping_folder()

    options = [RootSourcePath(context.current_path)] + get_initial_options(
        context.settings
    )
    mapping = Mapping(
        grid=ExampleJobParameterGrid(),
        options=options,
        description=f"Mapping created {datetime.date.today().strftime('%B %d %Y')} "
        f"by {getpass.getuser()}\n",
    )
    folder.save_mapping(mapping)
    click.echo(f"Initialised example mapping in {folder.DEFAULT_FILENAME}")


@click.command()
@pass_map_command_context
def delete(context: MapCommandContext):
    """delete mapping in current folder"""
    folder = context.get_current_mapping_folder()
    if not folder.has_mapping():
        raise ClickException("No mapping defined in current folder")
    folder.delete_mapping()
    click.echo(f"Removed mapping in current dir")


@handle_anonapi_exceptions
def get_mapping(context):
    return context.get_current_mapping()


@click.command()
@pass_map_command_context
@click.argument("path", type=click.Path(exists=True))
@click.option(
    "--check-dicom/--no-check-dicom",
    default=True,
    help="Open each file to check whether it is valid DICOM. Turning this off is "
    "faster, but the anonymization fails if non-DICOM files are included. "
    "On by default",
)
def add_study_folder(context: MapCommandContext, path, check_dicom):
    """Add all dicom files in given folder to map
    """

    mapping = add_path_to_mapping_click(
        Path(path),
        get_mapping(context),
        cwd=context.current_path,
        check_dicom=check_dicom,
    )
    context.get_current_mapping_folder().save_mapping(mapping)
    click.echo(f"Done. Added '{path}' to mapping")


def add_path_to_mapping_click(
    path: Path, mapping: Mapping, check_dicom: bool = True, cwd: Optional[Path] = None
):
    """Create a fileselection in the given path and add it to the given mapping

    Meant to be called from a click function. Contains calls to click.echo().
    Parameters
    ----------
    path: Path
        Path to create fileselection in
    mapping: Mapping
        Mapping to add the fileselection to
    check_dicom: bool, optional
        open each file to see whether it is valid DICOM. Setting False is faster
        but could include files that will fail the job in IDIS. Defaults to True
    cwd: Optional[Path]
        Current working directory. If given, write to mapping relative to this
        path

    Raises
    ------
    ValueError
        When path is absolute and does not start with cwd

    Returns
    -------
    Mapping
        The mapping with path added
    """
    # create a selection from all dicom files in given root_path
    file_selection = create_dicom_selection_click(path, check_dicom)

    # make path relative if requested
    if cwd:
        path = file_selection.data_file_path
        if path.is_absolute():
            file_selection.data_file_path = path.relative_to(cwd)

    # how to refer to this new file selection
    file_selection_identifier = FileSelectionIdentifier.from_object(file_selection)

    patient_name = f"autogenerated_{''.join(random.choices(string.ascii_uppercase + string.digits, k=5))}"
    patient_id = "auto_" + "".join(map(str, random.choices(range(10), k=8)))
    description = f"auto generated_{datetime.date.today().strftime('%B %d, %Y')}"
    row = [
        SourceIdentifierParameter(file_selection_identifier),
        PatientName(patient_name),
        PatientID(patient_id),
        Description(description),
    ]
    mapping.grid.rows.append(row)
    return mapping


@click.command()
@pass_map_command_context
@click.argument("pattern")
@click.option(
    "--check-dicom/--no-check-dicom",
    default=True,
    help="Open each file to check whether it is valid DICOM. Turning this off is "
    "faster, but the anonymization fails if non-DICOM files are included. "
    "On by default",
)
def add_all_study_folders(context: MapCommandContext, pattern, check_dicom):
    """Add all folders matching pattern to mapping
    """
    # Examples: **/* */1 */*/*2
    found = [
        x.relative_to(context.current_path)
        for x in Path(context.current_path).glob(pattern)
        if x.is_dir()
    ]
    click.echo(
        f"Pattern '{pattern}' matches the following paths"
        f"matches the following paths:"
    )
    click.echo("\n".join([str(x) for x in found]))
    if not click.confirm(
        f"This will add the {len(found)} folders listed above "
        f"to mapping. Are you sure?"
    ):
        click.echo("Cancelled")
        return
    else:
        mapping = get_mapping(context)
        for path in found:
            mapping = add_path_to_mapping_click(
                Path(path), mapping, cwd=context.current_path, check_dicom=check_dicom
            )

        context.get_current_mapping_folder().save_mapping(mapping)
        click.echo("Done")


@click.command()
@pass_map_command_context
@click.argument("selection", type=FileSelectionFileParam())
def add_selection(context: MapCommandContext, selection):
    """Add selection file to mapping
    """
    mapping = get_mapping(context)
    identifier = SourceIdentifierFactory().get_source_identifier_for_obj(selection)
    # make identifier root_path relative to mapping
    try:
        identifier.identifier = context.get_current_mapping_folder().make_relative(
            identifier.identifier
        )
    except MapperException as e:
        raise BadParameter(f"Selection file must be inside mapping folder:{e}")

    def random_string(k):
        return "".join(random.choices(string.ascii_uppercase + string.digits, k=k))

    def random_intstring(k):
        return str(map(str, random.choices(range(10), k=k)))

    def today():
        return datetime.date.today().strftime("%B %d, %Y")

    # add this selection to mapping
    mapping.add_row(
        [
            SourceIdentifierParameter(identifier),
            PatientName(f"autogenerated_{random_string(5)}"),
            PatientID(f"auto_{random_intstring(8)}"),
            Description(f"auto generated_" + today()),
        ]
    )

    context.get_current_mapping_folder().save_mapping(mapping)
    click.echo(f"Done. Added '{identifier}' to mapping")


@click.command()
@pass_map_command_context
def edit(context: MapCommandContext):
    """Edit the current mapping in OS default editor
    """
    mapping_folder = context.get_current_mapping_folder()
    if mapping_folder.has_mapping():
        click.launch(str(mapping_folder.full_path()))
    else:
        click.echo("No mapping file defined in current folder")


for func in [
    status,
    init,
    delete,
    add_study_folder,
    add_all_study_folders,
    edit,
    add_selection,
]:
    main.add_command(func)
