"""Click group and commands for the 'job' subcommand"""
import itertools
from typing import List

import click

from anonapi.cli.click_types import JobIDRangeParamType
from anonapi.cli.parser import command_group_function
from anonapi.context import AnonAPIContext
from anonapi.decorators import pass_anonapi_context, handle_anonapi_exceptions


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
def info(parser: AnonAPIContext, job_ids):
    """Print full info for one or more jobs"""
    # Each element in job_ids could be range. Flatten
    job_ids = flatten(job_ids)
    server = parser.get_active_server()
    for job_id in job_ids:
        job_info = parser.client_tool.get_job_info(server=server, job_id=job_id)
        click.echo(f"job {job_id} on {server.name}:")
        click.echo(job_info.as_string())


@command_group_function(name="list")
@handle_anonapi_exceptions
@click.argument("job_ids", type=JobIDRangeParamType(), nargs=-1)
def job_list(parser: AnonAPIContext, job_ids):
    """List info for multiple jobs"""
    if len(job_ids) == 0:  # handle empty nargs input gracefully
        click.echo("No job ids given")
        return
    job_ids = [x for x in itertools.chain(*job_ids)]  # make into one list
    server = parser.get_active_server()

    job_infos = parser.client_tool.get_job_info_list(
        server=server, job_ids=list(job_ids)
    )
    click.echo(job_infos.as_table_string())


@click.command()
@pass_anonapi_context
@click.argument("job_id", type=str)
def reset(parser: AnonAPIContext, job_id):
    """Reset job, process again"""
    server = parser.get_active_server()
    job_info = parser.client_tool.reset_job(server=server, job_id=job_id)
    click.echo(job_info)


@click.command()
@pass_anonapi_context
@click.argument("job_id", type=str)
@click.argument("reason", type=str)
def set_opt_out_ignore(parser: AnonAPIContext, job_id, reason):
    """Set opt-out ignore with given reason for job_id"""
    job_info = parser.client_tool.set_opt_out_ignore(
        server=parser.get_active_server(), job_id=job_id, reason=reason
    )
    click.echo(job_info)


@click.command()
@pass_anonapi_context
@click.argument("job_id", type=str)
def cancel(parser: AnonAPIContext, job_id):
    """Set job status to inactive"""
    server = parser.get_active_server()
    job_info = parser.client_tool.cancel_job(server=server, job_id=job_id)
    click.echo(job_info)


for func in [info, reset, cancel, job_list, set_opt_out_ignore]:
    main.add_command(func)
