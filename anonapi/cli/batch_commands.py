"""Click group and commands for the 'batch' subcommand
"""
import itertools
from typing import List

import click
from click.exceptions import ClickException

from anonapi.batch import JobBatch
from anonapi.cli.click_types import JobIDRangeParamType
from anonapi.client import ClientToolException
from anonapi.context import (
    AnonAPIContext,
    AnonAPIContextException,
    NoBatchDefinedException,
)
from anonapi.decorators import pass_anonapi_context, handle_anonapi_exceptions
from anonapi.responses import JobStatus, JobInfoColumns, JobInfo, format_job_info_list
from collections import Counter


@click.group(name="batch")
def main():
    """manage anonymization job batches"""
    pass


@click.command()
@pass_anonapi_context
def init(parser: AnonAPIContext):
    """Save an empty batch in the current folder, for current server"""
    batch_folder = parser.get_batch_folder()
    if batch_folder.has_batch():
        raise ClickException("Cannot init, A batch is already defined in this folder")
    else:
        server = parser.get_active_server()
        batch_folder.save(JobBatch(job_ids=[], server=server))
        click.echo(f"Initialised batch for {server} in current dir")


@click.command()
@pass_anonapi_context
def info(parser: AnonAPIContext):
    """Show batch in current directory"""
    try:
        click.echo(parser.get_batch().to_string())
    except NoBatchDefinedException as e:
        raise ClickException(str(e) + ". You can create one with 'anon batch init'")
    except AnonAPIContextException as e:
        raise ClickException(e)


@click.command()
@pass_anonapi_context
def delete(parser: AnonAPIContext):
    """delete batch in current folder"""
    parser.get_batch_folder().delete_batch()
    click.echo(f"Removed batch in current dir")


@click.command()
@pass_anonapi_context
@click.argument("job_ids", type=JobIDRangeParamType(), nargs=-1)
def add(parser: AnonAPIContext, job_ids):
    """Add ids to current batch. Space-separated (1 2 3) or range (1-40)
    """
    job_ids = [x for x in itertools.chain(*job_ids)]  # make into one list
    batch_folder = parser.get_batch_folder()
    batch: JobBatch = batch_folder.load()
    batch.job_ids = sorted(list(set(batch.job_ids) | set(job_ids)))
    batch_folder.save(batch)
    click.echo(f"Added {job_ids} to batch")


@click.command()
@pass_anonapi_context
@click.argument("job_ids", type=JobIDRangeParamType(), nargs=-1)
def remove(parser: AnonAPIContext, job_ids):
    """Remove ids from current batch. Space-separated (1 2 3) or range (1-40)
    """
    job_ids = [x for x in itertools.chain(*job_ids)]  # make into one list
    batch_folder = parser.get_batch_folder()
    batch: JobBatch = batch_folder.load()
    batch.job_ids = sorted(list(set(batch.job_ids) - set(job_ids)))
    batch_folder.save(batch)

    click.echo(f"Removed {job_ids} from batch")


@click.command()
@pass_anonapi_context
@handle_anonapi_exceptions
@click.option(
    "--patient-name/--no-patient-name",
    default=False,
    help="Add pseudo patient id to table",
)
def status(parser: AnonAPIContext, patient_name):
    """Print status overview for all jobs in batch"""

    batch = parser.get_batch()

    if patient_name:
        get_extended_info = True
    else:
        get_extended_info = False

    ids_queried = batch.job_ids

    infos = parser.client_tool.get_job_info_list(
        server=batch.server, job_ids=ids_queried, get_extended_info=get_extended_info,
    )

    click.echo(f"Job info for {len(infos)} jobs on {batch.server}:")
    columns_to_show = JobInfoColumns.DEFAULT_COLUMNS.copy()
    if patient_name:
        columns_to_show += [JobInfoColumns.pseudo_name]
    click.echo(infos.as_table_string(columns=columns_to_show))

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


@click.command()
@pass_anonapi_context
def reset(parser: AnonAPIContext):
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


@click.command()
@pass_anonapi_context
def cancel(parser: AnonAPIContext):
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


@click.command()
@handle_anonapi_exceptions
@pass_anonapi_context
def reset_error(parser: AnonAPIContext):
    """Reset all jobs with error status in the current batch"""
    batch: JobBatch = parser.get_batch()

    infos = parser.client_tool.get_job_info_list(
        server=batch.server, job_ids=batch.job_ids
    )

    job_ids = [x.job_id for x in infos if x.status == JobStatus.ERROR]

    if click.confirm(
        f"This will reset {len(job_ids)} jobs on {batch.server}. Are you sure?"
    ):
        for job_id in job_ids:
            click.echo(parser.client_tool.reset_job(server=batch.server, job_id=job_id))

        click.echo("Done")
    else:
        click.echo("User cancelled")


@click.command()
@handle_anonapi_exceptions
@pass_anonapi_context
def show_error(parser: AnonAPIContext):
    """Show full error message for all error jobs in batch"""
    batch: JobBatch = parser.get_batch()

    infos = parser.client_tool.get_job_info_list(
        server=batch.server, job_ids=batch.job_ids
    )

    error_infos: List[JobInfo] = [x for x in infos if x.status == JobStatus.ERROR]

    if error_infos:
        output = ""
        for info in error_infos:
            output += f"{format_job_info_list([info])}\n"
            output += "error message:\n"
            output += f"{info.error}\n\n"

        click.echo(output)
    else:
        click.echo("There are no jobs with error status in this batch")


for func in [
    info,
    status,
    reset,
    init,
    delete,
    add,
    remove,
    cancel,
    reset_error,
    show_error,
]:
    main.add_command(func)
