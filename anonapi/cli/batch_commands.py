"""Click group and commands for the 'batch' subcommand
"""
import itertools

import click

from anonapi.batch import JobBatch
from anonapi.cli.click_types import JobIDRangeParamType
from anonapi.cli.parser import (
    command_group_function,
    AnonCommandLineParser,
    AnonCommandLineParserException,
    NoBatchDefinedException,
    echo_error)
from anonapi.client import ClientToolException
from collections import Counter

from anonapi.responses import JobStatus


@click.group(name="batch")
def main():
    """manage anonymization job batches"""
    pass


@command_group_function()
def init(parser: AnonCommandLineParser,):
    """Save an empty batch in the current folder, for current server"""
    batch_folder = parser.get_batch_folder()
    if batch_folder.has_batch():
        raise AnonCommandLineParserException(
            "Cannot init, A batch is already defined in this folder"
        )
    else:
        server = parser.get_active_server()
        batch_folder.save(JobBatch(job_ids=[], server=server))
        click.echo(f"Initialised batch for {server} in current dir")


@command_group_function()
def info(parser: AnonCommandLineParser,):
    """Show batch in current directory"""
    try:
        click.echo(parser.get_batch().to_string())
    except NoBatchDefinedException as e:
        echo_error(str(e) + ". You can create one with 'anon batch init'")
    except AnonCommandLineParserException as e:
        echo_error(e)


@command_group_function()
def delete(parser: AnonCommandLineParser,):
    """delete batch in current folder"""
    parser.get_batch_folder().delete_batch()
    click.echo(f"Removed batch in current dir")


@command_group_function()
@click.argument("job_ids", type=JobIDRangeParamType(), nargs=-1)
def add(parser: AnonCommandLineParser, job_ids):
    """Add ids to current batch. Will not add already existing. Space separated, ranges like 1-40
    allowed
    """
    job_ids = [x for x in itertools.chain(*job_ids)]  # make into one list
    batch_folder = parser.get_batch_folder()
    batch: JobBatch = batch_folder.load()
    batch.job_ids = sorted(list(set(batch.job_ids) | set(job_ids)))
    batch_folder.save(batch)
    click.echo(f"Added {job_ids} to batch")


@command_group_function()
@click.argument("job_ids", type=JobIDRangeParamType(), nargs=-1)
def remove(parser: AnonCommandLineParser, job_ids):
    """Remove ids from current batch. Space separated, ranges like 1-40 allowed
    """
    job_ids = [x for x in itertools.chain(*job_ids)]  # make into one list
    batch_folder = parser.get_batch_folder()
    batch: JobBatch = batch_folder.load()
    batch.job_ids = sorted(list(set(batch.job_ids) - set(job_ids)))
    batch_folder.save(batch)

    click.echo(f"Removed {job_ids} from batch")


@command_group_function()
def status(parser: AnonCommandLineParser,):
    """Print status overview for all jobs in batch"""
    try:
        batch = parser.get_batch()
    except NoBatchDefinedException as e:
        echo_error(e)
        return

    ids_queried = batch.job_ids
    try:
        infos = parser.client_tool.get_job_info_list(
            server=batch.server, job_ids=ids_queried
        )
    except ClientToolException as e:
        echo_error(e)
        return

    click.echo(f"Job info for {len(infos)} jobs on {batch.server}:")
    click.echo(infos.as_table_string())

    summary = ["Status       count   percentage", "-------------------------------"]
    status_count = Counter([x.status for x in infos])
    status_count["NOT_FOUND"] = len(ids_queried) - len(infos)
    for key, value in status_count.items():
        percentage = f"{(value / len(ids_queried) * 100):.1f} %"
        msg = f"{key:<12} {str(value):<8} {percentage:<8}"
        summary.append(msg)

    summary.append("-------------------------------")
    summary.append(f"Total        {str(len(ids_queried)):<8} 100%")

    click.echo(f"Summary for all {len(ids_queried)} jobs:")
    click.echo("\n".join(summary))


@command_group_function()
def reset(parser: AnonCommandLineParser,):
    """Reset every job in the current batch"""
    batch: JobBatch = parser.get_batch()

    if click.confirm(
        f"This will reset {len(batch.job_ids)} jobs on {batch.server}. Are you sure?"
    ):
        for job_id in batch.job_ids:
            click.echo(parser.client_tool.reset_job(server=batch.server, job_id=job_id))

        click.echo("Done")
    else:
        click.echo("User cancelled")


@command_group_function()
def cancel(parser: AnonCommandLineParser,):
    """Cancel every job in the current batch"""
    batch: JobBatch = parser.get_batch()

    if click.confirm(
        f"This will cancel {len(batch.job_ids)} jobs on {batch.server}. Are you sure?"
    ):
        for job_id in batch.job_ids:
            click.echo(
                parser.client_tool.cancel_job(server=batch.server, job_id=job_id)
            )

        click.echo("Done")
    else:
        click.echo("User cancelled")


@command_group_function()
def reset_error(parser: AnonCommandLineParser,):
    """Reset all jobs with error status in the current batch"""
    batch: JobBatch = parser.get_batch()
    try:
        infos = parser.client_tool.get_job_info_list(
            server=batch.server, job_ids=batch.job_ids
        )
    except ClientToolException as e:
        echo_error(f"Error resetting: {str(e)}")
        return

    job_ids = [x.job_id for x in infos if x.status == JobStatus.ERROR]

    if click.confirm(
        f"This will reset {len(job_ids)} jobs on {batch.server}. Are you sure?"
    ):
        for job_id in job_ids:
            click.echo(parser.client_tool.reset_job(server=batch.server, job_id=job_id))

        click.echo("Done")
    else:
        click.echo("User cancelled")


for func in [info, status, reset, init, delete, add, remove, cancel, reset_error]:
    main.add_command(func)
