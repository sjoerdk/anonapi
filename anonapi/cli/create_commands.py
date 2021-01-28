"""Click group and commands for the 'create' subcommand"""
import logging
from typing import Dict, List, Optional
from pathlib import Path, PureWindowsPath

import click

from click.exceptions import Abort, ClickException
from anonapi.batch import BatchFolder, JobBatch
from anonapi.context import AnonAPIContext
from anonapi.client import APIClientException
from anonapi.decorators import pass_anonapi_context, handle_anonapi_exceptions
from anonapi.exceptions import AnonAPIException
from anonapi.mapper import MapperException, Mapping, MappingFile
from anonapi.parameters import (
    Parameter,
    DestinationPath,
    PseudoID,
    PseudoName,
    Project,
    Description,
    SourceIdentifierParameter,
    PIMSKey,
    ParameterSet,
    RootSourcePath,
    is_unc_path,
    get_legacy_idis_value,
)
from anonapi.persistence import PersistenceException
from anonapi.testresources import JobInfoFactory


logger = logging.getLogger(__name__)


class JobParameterSet(ParameterSet):
    """A collection of parameters that should create one job.

    Offers validation and mapping to job-creation function keywords
    """

    # keywords to use for each Parameter.
    PARAMETER_KEYWORDS = {
        DestinationPath: "destination_path",
        PseudoID: "anon_id",
        PseudoName: "anon_name",
        Project: "project_name",
        Description: "description",
        PIMSKey: "pims_keyfile_id",
    }

    # these types of parameters are never sent to a function directly. They
    # should be ignored when casting to kwargs
    NON_KEYWORD_PARAMETERS = [RootSourcePath]

    def __init__(
        self, parameters: List[Parameter], default_parameters: List[Parameter] = None
    ):
        """

        Parameters
        ----------
        parameters: List[Parameter]
            The parameters in this set
        default_parameters: List[Parameter]
            Include these parameters, unless overwritten in parameters
        """
        if default_parameters is None:
            default_parameters = []
        super().__init__(parameters=default_parameters)
        self.update(parameters)

    @classmethod
    def is_non_keyword(cls, parameter):
        """Is this parameter of a type that is never sent as a parameter directly?"""
        return any(isinstance(parameter, x) for x in cls.NON_KEYWORD_PARAMETERS)

    def get_source(self) -> Optional[SourceIdentifierParameter]:
        """Get the parameter indicating the source of the data"""
        return self.get_param_by_type(SourceIdentifierParameter)

    def as_kwargs(self) -> Dict[str, Parameter]:
        """Parameters as keyword arguments

        Raises
        ------
        ParameterMappingException
            If not all parameters can be mapped

        Returns
        -------
        Dict[str: Parameter]
            Job creation function parameter: Parameter dict
            This can be put into a creation function with **as_kwargs(params)

        """
        dict_out = {}

        # make all parameter paths absolute
        try:
            absolute_parameters = self.make_unc_paths(self.parameters)
        except NoAbsoluteRootPathException as e:
            raise ParameterMappingException(e)

        for parameter in absolute_parameters:
            if self.is_non_keyword(parameter):
                # This parameter should not be included in kwargs. Skip
                continue
            elif self.is_source_identifier(parameter):
                if self.is_pacs_type(parameter):
                    dict_out["source_instance_id"] = get_legacy_idis_value(
                        parameter.value
                    )
                elif self.is_path_type(parameter):
                    dict_out["source_path"] = str(parameter.value)
                else:
                    raise ParameterMappingException(
                        f"Unknown source parameter '{parameter}'"
                    )
            else:
                try:
                    dict_out[self.PARAMETER_KEYWORDS[type(parameter)]] = str(
                        parameter.value
                    )
                except KeyError:
                    raise ParameterMappingException(f"Unknown parameter '{parameter}'")

        return dict_out

    def fill_missing_parameters(self):
        """Pseudo name and Pseudo ID have become almost interchangeable. It makes no
        sense to set one and not the other. Make sure values are sane. Namely:
        id set, name none -> rename to id
        id none, name set -> rename to name
        id none, name none -> keep as is
        id set , name set -> keep as is
        """
        pseudo_id = self.get_param_by_type(PseudoID)
        pseudo_name = self.get_param_by_type(PseudoName)
        if pseudo_id is None and pseudo_name is not None:
            self.parameters.append(PseudoID(pseudo_name.value))  # take name for both
        elif pseudo_name is None and pseudo_id is not None:
            self.parameters.append(PseudoName(pseudo_id.value))  # take id for both

    def has_path_source(self) -> bool:
        """Set of parameters defines a source that is a path"""

        return any(self.is_path_type(x) for x in self.parameters)

    def validate(self):
        """Assert that this set can be used to create a job

        Raises
        ------
        JobSetValidationError
            If this set has problems or is missing required values
        """

        for required in [SourceIdentifierParameter, DestinationPath, Project]:
            if not self.get_param_by_type(required):
                raise JobSetValidationError(f"Missing required parameter {required}")

        if not self.has_path_source():
            # If this set has no path source, root source does not matter
            _, params = self.split_parameter(type_in=RootSourcePath)
        else:
            params = self.parameters
        try:
            self.make_unc_paths(params)
        except ParameterMappingException as e:
            raise JobSetValidationError(
                f"Error: {e}. Source and destination need to be absolute windows"
                f" paths."
            )

    def make_unc_paths(self, parameters: List[Parameter]):
        """A copy of this JobParameterSet where all paths are absolute UNC
        paths. No relative paths, no mapped drive letters

        Raises
        ------
        ParameterMappingException
            If there are relative paths that cannot be resolved or are not unc
        """
        # make sure that all relative paths can be resolved
        absolute_params = []
        for param in parameters:
            if hasattr(param, "path") and param.path:
                # TODO code smell. Does this random info have to be checked here?
                # rewrite
                # there is a path, try to make absolute and check unc
                if not param.path.is_absolute():
                    param = param.as_absolute(self.get_absolute_root_path())
                if not is_unc_path(param.path):
                    raise ParameterMappingException(
                        f"{param} is not a unc path. It will not be clear where this "
                        f"path is outside the current computer"
                    )
            absolute_params.append(param)

        return absolute_params

    def get_absolute_root_path(self) -> PureWindowsPath:
        """From this set, get the root path

        Raises
        ------
        NoAbsoluteRootPathException
            If there are relative paths that cannot be resolved

        """
        root_path = self.get_param_by_type(RootSourcePath)
        if not root_path:
            raise NoAbsoluteRootPathException("No absolute root root_path defined")
        elif not root_path.path.is_absolute():
            raise NoAbsoluteRootPathException(
                f"Root root_path {root_path} is not absolute"
            )
        else:
            return root_path.value


class CreateCommandsContext(AnonAPIContext):
    """Passed to all methods in the create group. Contains some additional methods
    over general context instance

    """

    def __init__(self, context: AnonAPIContext):
        super().__init__(
            client_tool=context.client_tool,
            settings=context.settings,
            current_dir=context.current_dir,
        )

    def default_parameters(self) -> List[Parameter]:
        """Default parameters from settings"""
        return self.settings.job_default_parameters

    def create_job_for_element(self, parameters: List[Parameter]) -> str:
        """Create a job for the given parameters

        Parameters
        ----------
        parameters: List[Parameter]
            The parameters to use

        Raises
        ------
        JobCreationException
            If creating jobs fails for any reason

        Returns
        -------
        str
            job id created
        """

        row = JobParameterSet(parameters)
        source = row.get_source()
        if not source:
            raise JobCreationException(
                "No source identifier found. I can't create a job without knowing"
                " where to get the data"
            )

        try:
            if row.is_pacs_type(source):
                response = self.client_tool.create_pacs_job(
                    server=self.get_active_server(), **row.as_kwargs()
                )
            elif row.is_path_type(source):
                response = self.client_tool.create_path_job(
                    server=self.get_active_server(), **row.as_kwargs()
                )
            else:
                raise JobCreationException(f"Unknown source '{source}'")

        except (APIClientException, PersistenceException) as e:
            raise JobCreationException(f"Error creating job for source {source}: {e}")

        return str(response.job_id)

    def add_to_batch(self, created_job_ids):
        """Add job ids as batch in current dir. If batch does not exist, create"""
        batch_folder = BatchFolder(path=self.current_dir)
        if batch_folder.has_batch():
            batch: JobBatch = batch_folder.load()
        else:
            batch = JobBatch(job_ids=[], server=self.get_active_server())
        if batch.server.url != self.get_active_server().url:
            logger.info(
                "A batch exists in this folder, but for a different server. "
                "Not saving job ids in batch"
            )
        else:
            logger.info("Saving job ids in batch in current folder")
            batch.job_ids = sorted(
                list(set(batch.job_ids) | set(created_job_ids))
            )  # add only unique new ids
            batch_folder.save(batch)

    def active_mapping_file_path(self) -> Optional[Path]:
        return self.settings.active_mapping_file

    def get_current_mapping_file(self) -> MappingFile:
        if not self.active_mapping_file_path():
            raise MapperException("No active mapping")
        return MappingFile(self.settings.active_mapping_file)

    def get_mapping(self) -> Mapping:
        return self.get_current_mapping_file().get_mapping()


pass_create_commands_context = click.make_pass_decorator(CreateCommandsContext)


@click.group(name="create")
@click.pass_context
@pass_anonapi_context
def main(context: AnonAPIContext, ctx):
    """Create jobs"""
    ctx.obj = CreateCommandsContext(context=context)


def mock_create(*args, **kwargs):
    """Job creation method that does not hit any server, just prints to console"""
    logger.info("create was called with rows:")
    logger.info("\n".join(args))
    logger.info("\n".join(map(str, kwargs.items())))
    return JobInfoFactory(job_id=-1)  # a mocked response


@click.command()
@pass_create_commands_context
@handle_anonapi_exceptions
@click.option(
    "--dry-run/--no-dry-run", default=False, help="Do not post to server, just print"
)
def from_mapping(context: CreateCommandsContext, dry_run):
    """Create jobs from mapping in current folder"""
    if dry_run:
        logger.info("** Dry run, nothing will be sent to server **")

        # Make sure no jobs are actually created
        context.client_tool.create_path_job = mock_create
        context.client_tool.create_pacs_job = mock_create

    job_sets = extract_job_sets(context.default_parameters(), context.get_mapping())

    # inspect project name and destination to present the next question to the user
    project_names = set()
    destination_paths = set()
    for job_set in job_sets:
        project_names.add(job_set.get_param_by_type(Project).value)
        destination_paths.add(job_set.get_param_by_type(DestinationPath).value)

    question = (
        f"This will create {len(job_sets)} jobs on {context.get_active_server().name},"
        f" for projects '{list(project_names)}', writing data to "
        f"'{[str(x) for x in destination_paths]}'. Are you sure?"
    )
    if not click.confirm(question):
        logger.info("Cancelled")
        return

    created_job_ids = create_jobs(context, job_sets)

    if created_job_ids:
        context.add_to_batch(created_job_ids)

    logger.info("Done")


def create_jobs(
    context: CreateCommandsContext, job_sets: List[JobParameterSet]
) -> List[str]:
    """Create an anonymization job for each parameter set

    Notes
    -----
    Will stop creating when hitting problems like not being able to reach the server
    In that case results are returned for any created jobs up to the exception

    Returns
    -------
    List[str]
        Job ids for each created job
    """
    created_job_ids = []
    for job_set in job_sets:
        try:
            job_id = context.create_job_for_element(job_set.parameters)
            logger.info(f"Created job with id {job_id}")
            created_job_ids.append(job_id)
        except JobCreationException as e:
            logger.info(str(e))
            logger.info(
                "Error will probably keep occurring. Stopping further job creation."
            )
            break
    logger.info(f"created {len(created_job_ids)} jobs: {created_job_ids}")
    return created_job_ids


def extract_job_sets(
    default_parameters: List[Parameter], mapping: Mapping
) -> List[JobParameterSet]:
    """Extract sets of parameters each creating one job

    Parameters
    ----------
    default_parameters: List[Parameter]
        These parameters will always be included for each job
    mapping: Mapping
        Extract from this mapping

    Raises
    ------
    JobSetValidationError
        When mapping contains sets that can not be made into a job

    Returns
    -------
    List[JobParameterSet]
    """
    # add defaults to each row
    job_sets = [
        JobParameterSet(row, default_parameters=default_parameters)
        for row in mapping.rows
    ]
    # validate each job set and fill missing values
    for job_set in job_sets:
        job_set.fill_missing_parameters()
        try:
            job_set.validate()
        except JobSetValidationError as e:
            raise ClickException(f"Error validating parameters: {e}")
    return job_sets


@click.command()
@pass_create_commands_context
def set_defaults(context: CreateCommandsContext):
    """Set project name used when creating jobs"""
    job_default_parameters: List[Parameter] = context.settings.job_default_parameters
    logger.info(
        "Please set default rows current value shown in [brackets]. Pressing enter"
        " without input will keep current value"
    )
    try:
        project_name = click.prompt(
            f"Please enter default IDIS project name:",
            show_default=True,
            default=job_default_parameters.project_name,
        )

        destination_path = click.prompt(
            f"Please enter default job destination directory:",
            show_default=True,
            default=job_default_parameters.destination_path,
        )
    except Abort:
        logger.info("Cancelled")

    job_default_parameters.project_name = project_name
    job_default_parameters.destination_path = destination_path
    context.settings.save_to()
    logger.info("Saved")


@click.command()
@pass_create_commands_context
def show_defaults(context: CreateCommandsContext):
    """Show project name used when creating jobs"""
    logger.info("Default parameters when creating jobs:")
    for parameter in context.settings.job_default_parameters:
        logger.info(parameter.describe())


for func in [from_mapping, set_defaults, show_defaults]:
    main.add_command(func)


class JobCreationException(APIClientException):
    pass


class ParameterMappingException(AnonAPIException):
    pass


class NoAbsoluteRootPathException(ParameterMappingException):
    pass


class JobSetValidationError(AnonAPIException):
    pass
