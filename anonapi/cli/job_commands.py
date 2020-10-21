"""Click group and commands for the 'job' subcommand"""
import itertools
import logging
from typing import List

import click

from anonapi.cli.click_parameter_types import JobIDRangeParamType
from anonapi.context import AnonAPIContext, command_group_function
from anonapi.decorators import pass_anonapi_context, handle_anonapi_exceptions

logger = logging.getLogger(__name__)


def flatten(list_of_lists: List[List]) -> List:
    """Take all lists in list and add all elements together in one flat list"""
    return [item for sublist in list_of_lists for item in sublist]


@click.group(name="job")
def main():
    """Manage anonymization jobs"""
    pass


@click.command()
@pass_anonapi_context
@handle_anonapi_exceptions
@click.argument("job_ids", type=JobIDRangeParamType(), nargs=-1)
def info(context: AnonAPIContext, job_ids):
    """Print full info for one or more jobs"""
    # Each element in job_ids could be range. Flatten
    job_ids = flatten(job_ids)
    server = context.get_active_server()
    for job_id in job_ids:
        job_info = context.client_tool.get_job_info(server=server, job_id=job_id)
        logger.info(f"job {job_id} on {server.name}:")
        logger.info(job_info.as_string())


@command_group_function(name="list")
@handle_anonapi_exceptions
@click.argument("job_ids", type=JobIDRangeParamType(), nargs=-1)
def job_list(context: AnonAPIContext, job_ids):
    """List info for multiple jobs"""
    if len(job_ids) == 0:  # handle empty nargs input gracefully
        logger.info("No job ids given")
        return
    job_ids = [x for x in itertools.chain(*job_ids)]  # make into one list
    server = context.get_active_server()

    job_infos = context.client_tool.get_job_info_list(
        server=server, job_ids=list(job_ids)
    )
    logger.info(job_infos.as_table_string())


@click.command()
@pass_anonapi_context
@click.argument("job_id", type=str)
def reset(context: AnonAPIContext, job_id):
    """Reset job, process again"""
    server = context.get_active_server()
    job_info = context.client_tool.reset_job(server=server, job_id=job_id)
    logger.info(job_info)


@click.command()
@pass_anonapi_context
@click.argument("job_id", type=str)
@click.argument("reason", type=str)
def set_opt_out_ignore(context: AnonAPIContext, job_id, reason):
    """Set opt-out ignore with given reason for job_id"""
    job_info = context.client_tool.set_opt_out_ignore(
        server=context.get_active_server(), job_id=job_id, reason=reason
    )
    logger.info(job_info)


@click.command()
@pass_anonapi_context
@click.argument("job_id", type=str)
def cancel(context: AnonAPIContext, job_id):
    """Set job status to inactive"""
    server = context.get_active_server()
    job_info = context.client_tool.cancel_job(server=server, job_id=job_id)
    logger.info(job_info)


for func in [info, reset, cancel, job_list, set_opt_out_ignore]:
    main.add_command(func)
