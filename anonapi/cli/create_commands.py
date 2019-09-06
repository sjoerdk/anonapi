"""Click group and commands for the 'create' subcommand
"""
import json

import click
from click.exceptions import Abort
from fileselection.fileselection import FileSelectionFolder

from anonapi.batch import BatchFolder, JobBatch
from anonapi.cli.parser import command_group_function, AnonCommandLineParser
from anonapi.client import APIClientException
from anonapi.mapper import (
    MappingListFolder,
    MappingLoadError,
    FileSelectionFolderIdentifier,
    AnonymizationParameters,
    PathIdentifier, FileSelectionIdentifier)
from anonapi.settings import JobDefaultParameters, AnonClientSettingsException


class MappingElement:
    """A single line in a mapping

    Notes
    -----
    A mapping is a dictionary, but its annoying to pass around key+value"""

    def __init__(self, source, parameters):
        """

        Parameters
        ----------
        source: SourceIdentifier
        parameters: AnonymizationParameters
        """
        self.source = source
        self.parameters = parameters

    def as_dict(self):
        return {**{'source': str(self.source)}, **self.parameters.as_dict()}

    def get_description(self):
        """Human readable description of this element"""
        return json.dumps(self.as_dict(), indent=2)


class CreateCommandsContext:
    """Passed to all methods in the create group. Contains some additional methods over general parser instance

    """

    def __init__(self, parser: AnonCommandLineParser):
        self.parser = parser

    def create_job_for_element(self, element: MappingElement):
        """Create a job for the given source and parameters

        Parameters
        ----------
        element: MappingElement

        Raises
        ------
        AnonClientSettingsException
            If job creation fails due to missing settings
        JobCreationException
            If creating jobs fails for any other reason

        Returns
        -------
        int
            job id created
        """

        project_name, destination_path = get_default_parameters(
            self.parser.settings.job_default_parameters
        )

        if issubclass(type(element.source), PathIdentifier):
            try:
                parameters = assert_job_parameters(element.parameters)
                response = self.parser.client_tool.create_path_job(
                    anon_id=parameters.patient_id,
                    server=self.parser.get_active_server(),
                    anon_name=parameters.patient_name,
                    project_name=project_name,
                    source_path=str(element.source),
                    destination_path=str(destination_path),
                    description=parameters.description,
                )
            except (APIClientException, AnonClientSettingsException) as e:
                raise JobCreationException(
                    f"Error creating job for source {element.source}: {e}"
                )

        else:
            raise JobCreationException(
                f"Cannot create job for source type {type(element.source)}"
            )

        return response["job_id"]

    def add_to_batch(self, created_job_ids):
        """Add job ids as batch in current dir. If batch does not exist, create"""
        parser = self.parser
        batch_folder = BatchFolder(path=parser.current_dir())
        if batch_folder.has_batch():
            batch: JobBatch = batch_folder.load()
        else:
            batch = JobBatch(job_ids=[], server=parser.get_active_server())
        if batch.server.url != parser.get_active_server().url:
            click.echo(
                "A batch exists in this folder, but for a different server. Not saving job ids in batch"
            )
        else:
            click.echo("Saving job ids in batch in current folder")
            batch.job_ids = sorted(
                list(set(batch.job_ids) | set(created_job_ids))
            )  # add only unique new ids
            batch_folder.save(batch)


@click.group(name="create")
@click.pass_context
def main(ctx):
    """create jobs"""
    parser = ctx.obj
    ctx.obj = CreateCommandsContext(parser=parser)


def make_absolute(elements, root_path):
    """Make sure path elements that are relative are made absolute by prepending root_path.

    Parameters
    ----------
    elements: List[MappingElement]
    root_path: Path

    Returns
    -------
    List[MappingElement]
    """

    path_elements = [x for x in elements if issubclass(type(x.source), PathIdentifier)]
    for x in path_elements:
        x.source.identifier = root_path / x.source.identifier

    return elements


def convert_to_fileselection(elements):
    """Convert path element to make them less ambiguous.

    Convert FileSelectionFolderIdentifier (refers to a whole folder, assumes actual file name is default) to
    a FileSelectionIdentifier that refers explicitly to a single file. This makes it less vague what the source for
    files actually is

    Parameters
    ----------
    elements: List[MappingElement]

    Returns
    -------
    List[MappingElement]
    """

    for element in [x for x in elements if type(x.source) == FileSelectionFolderIdentifier]:
        folder = FileSelectionFolder(path=element.source.identifier)
        element.source = FileSelectionIdentifier(identifier=folder.get_data_file_path())

    return elements


@command_group_function()
@click.option('--dry-run/--no-dry-run', default=False, help="Do not post to server, just print")
def from_mapping(context: CreateCommandsContext, dry_run):
    """Create jobs from mapping in current folder"""
    if dry_run:
        click.echo("** Dry run, nothing will be sent to server **")
    parser = context.parser
    try:
        mapping = MappingListFolder(parser.current_dir()).get_mapping()
    except MappingLoadError as e:
        click.echo(e)
        return

    try:
        project_name, destination_path = get_default_parameters(
            parser.settings.job_default_parameters
        )
    except AnonClientSettingsException as e:
        click.echo(f"{e}. Please use set-defaults te set them")
        return  # Without these parameters jobs cannot be created. Stop loop

    question = (
        f"This will create {len(mapping)} jobs on {parser.get_active_server().name}, for "
        f'project "{project_name}", writing data to "{destination_path}". Are you sure?'
    )
    if not click.confirm(question):
        click.echo("Cancelled")
        return

    created_job_ids = []
    elements = [MappingElement(x, y) for x, y in mapping.items()]
    elements = convert_to_fileselection(make_absolute(elements, parser.current_dir()))
    for element in elements:
        if dry_run:
            click.echo(element.get_description())
        else:
            try:
                job_id = context.create_job_for_element(element)
                click.echo(f"Created job with id {job_id}")
                created_job_ids.append(job_id)
            except JobCreationException as e:
                click.echo(e)
                break  # error will probably keep occurring. Stop loop

    click.echo(f"created {len(created_job_ids)} jobs: {created_job_ids}")

    if created_job_ids:
        context.add_to_batch(created_job_ids)

    click.echo("Done")


@command_group_function()
def set_defaults(context: CreateCommandsContext):
    """Set project name used when creating jobs"""
    job_default_parameters: JobDefaultParameters = context.parser.settings.job_default_parameters
    click.echo("Please set default parameters current value shown in [brackets]. Pressing enter without input will keep"
               "current value")
    try:
        project_name = click.prompt(
            f"Please enter default IDIS project name:",
            show_default=True,
            default=job_default_parameters.project_name
        )

        destination_path = click.prompt(
            f"Please enter default job destination directory:",
            show_default=True,
            default=job_default_parameters.destination_path
        )
    except Abort:
        click.echo("Cancelled")

    job_default_parameters.project_name = project_name
    job_default_parameters.destination_path = destination_path
    context.parser.settings.save()
    click.echo("Saved")


@command_group_function()
def show_defaults(context: CreateCommandsContext):
    """show project name used when creating jobs"""

    job_default_parameters: JobDefaultParameters = context.parser.settings.job_default_parameters
    click.echo(f"default IDIS project name: {job_default_parameters.project_name}")
    click.echo(f"default job destination directory: {job_default_parameters.destination_path}")


for func in [from_mapping, set_defaults, show_defaults]:
    main.add_command(func)


def assert_job_parameters(parameters: AnonymizationParameters):
    """Make sure all fields in parameters are filled.

    When read from disk, certain parameters might be None. Fill these.

    Parameters
    ----------
    parameters: AnonymizationParameters
        parameters object that might have None values

    Returns
    -------
    parameters: AnonymizationParameters
        parameters object where all fields are filled
    """
    if not parameters.patient_name:
        parameters.patient_name = parameters.field_names

    if parameters.description is None:
        parameters.patient_name = ""

    return parameters


def get_default_parameters(job_default_parameters: JobDefaultParameters):
    """Make sure default parameters are all present. Raise exception if not

    Parameters
    ----------
    job_default_parameters: JobDefaultParameters

    Raises
    ------
    AnonClientSettingsException
        When a parameter is not found or is empty

    Returns
    -------
    (str, Path)
        project_name, destination_path

    """
    if not job_default_parameters.project_name:
        raise AnonClientSettingsException(
            "Could not find default project name in settings"
        )
    if not job_default_parameters.destination_path:
        raise AnonClientSettingsException(
            "Could not find default project name in settings"
        )
    return job_default_parameters.project_name, job_default_parameters.destination_path


class JobCreationException(APIClientException):
    pass
