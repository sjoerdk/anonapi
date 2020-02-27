"""Click group and commands for the 'job' subcommand
"""
import itertools

import click

from anonapi.cli.click_types import JobIDRangeParamType
from anonapi.cli.parser import command_group_function
from anonapi.context import AnonAPIContext
from anonapi.client import ClientToolException
from anonapi.decorators import pass_anonapi_context, handle_anonapi_exceptions


@click.group(name="job")
def main():
    """manage anonymization jobs"""
    pass


@click.command()
@pass_anonapi_context
@handle_anonapi_exceptions
@click.argument("job_id", type=str)
def info(parser: AnonAPIContext, job_id):
    """print job info
    """
    server = parser.get_active_server()
    job_info = parser.client_tool.get_job_info(server=server, job_id=job_id)
    click.echo(f"job {job_id} on {server.name}:")
    click.echo(job_info.as_string())


@command_group_function(name="list")
@handle_anonapi_exceptions
@click.argument("job_ids", type=JobIDRangeParamType(), nargs=-1)
def job_list(parser: AnonAPIContext, job_ids):
    """list info for multiple jobs
    """
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
    """reset job, process again
    """
    server = parser.get_active_server()
    job_info = parser.client_tool.reset_job(server=server, job_id=job_id)
    click.echo(job_info)


@click.command()
@pass_anonapi_context
@click.argument("job_id", type=str)
def cancel(parser: AnonAPIContext, job_id):
    """set job status to inactive """
    server = parser.get_active_server()
    job_info = parser.client_tool.cancel_job(server=server, job_id=job_id)
    click.echo(job_info)


for func in [info, reset, cancel, job_list]:
    main.add_command(func)
