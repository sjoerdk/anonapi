"""Click group and commands for the 'map' subcommand"""
import logging
import os
from pathlib import Path
from typing import List, Optional

import click
import datetime
import getpass
import random
import string

from click.exceptions import BadParameter

from anonapi.cli.click_parameter_types import (
    AccessionNumberFile,
    FileSelectionFileParam,
    PathParameterFile,
    WildcardFolder,
)
from anonapi.selection import create_dicom_selection
from anonapi.context import AnonAPIContext
from anonapi.decorators import pass_anonapi_context, handle_anonapi_exceptions
from anonapi.mapper import (
    DEFAULT_MAPPING_NAME,
    JobParameterGrid,
    MappingFile,
    ExampleJobParameterGrid,
    MapperException,
    Mapping,
    MappingParameterSet,
    get_local_dialect,
)
from anonapi.parameters import (
    AccessionNumber,
    ParameterSet,
    PathParameter,
    SourceIdentifierFactory,
    DestinationPath,
    PseudoName,
    SourceIdentifierParameter,
    PseudoID,
    Description,
    RootSourcePath,
    Project,
    Parameter,
    FileSelectionIdentifier,
)
from anonapi.settings import AnonClientSettings, DefaultAnonClientSettings

logger = logging.getLogger(__name__)


class MapCommandContext:
    def __init__(self, current_dir, settings: AnonClientSettings):
        self.current_dir = current_dir
        self.settings = settings

    def active_mapping_file_path(self) -> Optional[Path]:
        return self.settings.active_mapping_file

    def get_current_mapping_file(self) -> MappingFile:
        """Get active MappingFile object. If none is active raise exception

        Notes
        -----
        Active mapping file has not been parsed or even checked for existence.
        This method might return a MappingFile that points to a non-existant file
        or to a file with invalid Format. Use MappingFile.get_mapping() to be sure
        of existence and validity

        Returns
        -------
        MappingFile

        Raises
        ------
        MapperException
            If there is no active mapping file

        """
        if not self.active_mapping_file_path():
            raise MapperException(
                "No active mapping. Please " "use 'anon map active <mapping_file>'"
            )
        return MappingFile(self.settings.active_mapping_file)

    def get_current_mapping(self) -> Mapping:
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
        return self.get_current_mapping_file().get_mapping()


pass_map_command_context = click.make_pass_decorator(MapCommandContext)


@click.group(name="map")
@click.pass_context
@pass_anonapi_context
def main(context: AnonAPIContext, ctx):
    """Map original data to anonymized name, id, etc."""

    # both anonapi_context and base click ctx are passed to be able change ctx.obj
    ctx.obj = MapCommandContext(
        current_dir=context.current_dir, settings=context.settings
    )


@click.command()
@pass_map_command_context
@handle_anonapi_exceptions
def status(context: MapCommandContext):
    """Show mapping in current directory"""
    mapping_file = context.get_current_mapping_file()
    info = mapping_file.get_mapping().to_string()  # do this to fail early
    logger.info(f"Mapping at {mapping_file.file_path}")
    logger.info(info)


def get_initial_options(settings: AnonClientSettings) -> List[Parameter]:
    """Do the awkward determination of what initially to write in the options
    section of a new mapping
    """
    # baseline options as a dict
    options = {
        x.field_name: x
        for x in [
            Project("Wetenschap-Algemeen"),
            DestinationPath(r"\\server\share\folder"),
        ]
    }

    # if any are given, use these instead of baseline
    options.update({x.field_name: x for x in settings.job_default_parameters})

    return list(options.values())


@click.command()
@pass_map_command_context
@handle_anonapi_exceptions
def init(context: MapCommandContext):
    """Save a default mapping in a default location in the current folder"""
    mapping_file = MappingFile(Path(context.current_dir) / DEFAULT_MAPPING_NAME)
    mapping_file.save_mapping(create_empty_mapping(context))
    logger.info(f"Initialised example mapping in {mapping_file.file_path}")
    _activate(context.settings, mapping_path=mapping_file.file_path)


@click.command()
@pass_map_command_context
@handle_anonapi_exceptions
def activate(context: MapCommandContext):
    """All subsequent mapping actions will target this folder"""
    mapping_file_path = Path(context.current_dir) / DEFAULT_MAPPING_NAME
    if not mapping_file_path.exists():
        raise MapperException(
            f"Could not find mapping file at " f"'{mapping_file_path}'"
        )
    _activate(context.settings, mapping_path=mapping_file_path)


def _activate(settings: AnonClientSettings, mapping_path: Path):
    """Internal method called from multiple click methods"""
    settings.active_mapping_file = mapping_path
    settings.save()
    logger.info(f"Activated mapping at {mapping_path}")


def create_mapping(
    context: MapCommandContext = None, grid: JobParameterGrid = None
) -> Mapping:
    """Create a mapping with given parameter grid

    Parameters
    ----------
    context: MapCommandContext, optional
        set default options according to this context. Defaults to built-in
        defaults
    grid: JobParameterGrid, optional
        Include this parameter grid. Defaults to empty grid
    """
    if not context:
        context = MapCommandContext(
            current_dir=os.getcwd(), settings=DefaultAnonClientSettings()
        )
    options = [RootSourcePath(context.current_dir)] + get_initial_options(
        context.settings
    )
    mapping = Mapping(
        grid=grid,
        options=options,
        description=f"Mapping created {datetime.date.today().strftime('%B %d %Y')} "
        f"by {getpass.getuser()}\n",
        dialect=get_local_dialect(),
    )
    return mapping


def create_example_mapping(context: MapCommandContext = None) -> Mapping:
    """A default mapping with some example parameters

    Parameters
    ----------
    context: MapCommandContext, optional
        set default options according to this context. Defaults to built-in
        defaults
    """
    return create_mapping(context, ExampleJobParameterGrid())


def create_empty_mapping(context: MapCommandContext = None) -> Mapping:
    """A minimal, empty mapping

    Parameters
    ----------
    context: MapCommandContext, optional
        set default options according to this context. Defaults to built-in
        defaults
    """
    return create_mapping(context, JobParameterGrid(rows=[]))


@click.command()
@pass_map_command_context
@handle_anonapi_exceptions
def delete(context: MapCommandContext):
    """Delete current active mapping"""
    path = context.get_current_mapping_file().file_path
    try:
        os.remove(path)
        logger.info(f"Removed mapping at {path}")
    except FileNotFoundError as e:
        raise MapperException(f"Error deleting mapping: {e}")


@click.command()
@pass_map_command_context
@click.argument("paths", type=WildcardFolder(exists=True), nargs=-1)
@click.option(
    "-f",
    "--input-file",
    "input_file",
    type=PathParameterFile(),
    help="add all study folders in this xlsx or csv file to mapping. Looks "
    "for column 'folder' in file. If a column 'pseudoID' is present,"
    "adds these instead of auto-generating",
)
@click.option(
    "--check-dicom/--no-check-dicom",
    default=True,
    help="--check-dicom: Open each file to check whether it is valid DICOM. "
    "--no-check-dicom: Add all files that look like DICOM (exclude files with"
    " known file extensions like .txt or .xml). on by default",
)
@handle_anonapi_exceptions
def add_study_folders(context: MapCommandContext, paths, input_file, check_dicom):
    """Add all dicom files in given folders to mapping"""
    if input_file:
        # an input file was given and parsed already. Use the rows from that.
        # Split off the path to add from any other parameters in that row
        input_rows = {}
        for row in input_file.rows:
            path_param, rest = ParameterSet(row).split_parameter(PathParameter)
            input_rows[path_param.path] = rest

    else:
        # No file to add, add folders given as input.
        # flatten paths, which is a tuple (due to nargs -1) of lists (due to
        # wildcards)
        paths = [path for wildcard in paths for path in wildcard]
        input_rows = {path: [] for path in paths}

    logger.info(f"Adding {len(input_rows)} paths to mapping")

    mapping_file = context.get_current_mapping_file()
    mapping = mapping_file.get_mapping()
    for path, params in input_rows.items():
        logger.info(f"Adding '{path}' to mapping")
        fileselection = find_dicom_files(
            Path(path), cwd=context.current_dir, check_dicom=check_dicom
        )
        # assert this is a valid set of parameters and add defaults if needed
        mapping.grid.append_row(
            MappingParameterSet(parameters=[fileselection] + params).parameters
        )

        # save each time so we don't loose all when an error occurs
        mapping_file.save_mapping(mapping)
        logger.info("")  # extra newline makes separate folder adding more readable
    logger.info(f"Done. Added '{[str(x) for x in input_rows.keys()]}' to mapping")


@click.command()
@pass_map_command_context
@click.argument("accession_numbers", type=str, nargs=-1)
@click.option(
    "-f",
    "--input-file",
    "input_file",
    type=AccessionNumberFile(),
    help="add all accession numbers xlsx or csv file to mapping. Looks "
    "for column 'accession_number' in file. If a column 'pseudoID' is present,"
    "adds these instead of auto-generating pseudonym",
)
@handle_anonapi_exceptions
def add_accession_numbers(context: MapCommandContext, accession_numbers, input_file):
    """Add accession numbers to an existing mapping"""
    if input_file:
        # an input file was given and parsed already. Use the rows from that.
        # Split off the path to add from any other parameters in that row
        input_rows = []
        for row in input_file.rows:
            accession_number, rest = ParameterSet(row).split_parameter(AccessionNumber)
            input_rows.append(
                [SourceIdentifierParameter(accession_number.to_string(delimiter=":"))]
                + rest
            )
    else:
        # accession numbers were given in cli directly, make into source parameters
        input_rows = [
            [SourceIdentifierParameter(AccessionNumber(x).to_string(delimiter=":"))]
            for x in accession_numbers
        ]

    mapping_file = context.get_current_mapping_file()
    mapping = mapping_file.get_mapping()
    for row in input_rows:
        # assert this is a valid set of parameters and add defaults if needed
        logger.info(f"Adding {row[0].value}")
        mapping.grid.append_row(MappingParameterSet(parameters=row).parameters)

    mapping_file.save_mapping(mapping)
    logger.info(f"Done. Added {len(input_rows)} accession numbers")


def find_dicom_files(
    path: Path, check_dicom: bool = True, cwd: Optional[Path] = None
) -> SourceIdentifierParameter:
    """Finds all DICOM files in the given path and saves this as fileselection

    Parameters
    ----------
    path: Path
        Path to create fileselection in
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
    SourceIdentifierParameter
        A reference to the fileselection created
    """
    # create a selection from all dicom files in given root_path
    file_selection = create_dicom_selection(path, check_dicom)

    # make path relative if requested
    if cwd:
        path = file_selection.data_file_path
        if path.is_absolute():
            file_selection.data_file_path = path.relative_to(cwd)

    # how to refer to this new file selection
    return SourceIdentifierParameter.init_from_source_identifier(
        FileSelectionIdentifier.from_object(file_selection)
    )


@click.command()
@pass_map_command_context
@click.argument("selection", type=FileSelectionFileParam())
@handle_anonapi_exceptions
def add_selection(context: MapCommandContext, selection):
    """Add selection file to mapping"""
    mapping_file = context.get_current_mapping_file()
    mapping = mapping_file.get_mapping()
    identifier = SourceIdentifierFactory().get_source_identifier_for_obj(selection)
    # make identifier root_path relative to current dir
    try:
        # TODO: clean up identifier structure. The line below smells from yards away
        identifier.identifier = identifier.identifier.relative_to(context.current_dir)

    except ValueError as e:
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
            PseudoName(f"autogenerated_{random_string(5)}"),
            PseudoID(f"auto_{random_intstring(8)}"),
            Description(f"auto generated_" + today()),
        ]
    )

    mapping_file.save_mapping(mapping)
    logger.info(f"Done. Added '{identifier}' to mapping")


@click.command()
@pass_map_command_context
@handle_anonapi_exceptions
def edit(context: MapCommandContext):
    """Edit the active mapping in OS default editor"""
    path = context.get_current_mapping_file().file_path
    if path.exists():
        click.launch(str(path))
    else:
        raise MapperException(f"No mapping file found at {path}")


for func in [
    status,
    init,
    delete,
    add_study_folders,
    add_accession_numbers,
    edit,
    add_selection,
    activate,
]:
    main.add_command(func)
