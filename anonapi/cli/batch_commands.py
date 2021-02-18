"""Click group and commands for the 'batch' subcommand"""
import itertools
import logging
from typing import List

import click
from click.exceptions import ClickException

from anonapi.batch import BatchFolder, JobBatch
from anonapi.cli.click_parameter_types import JobIDRangeParamType
from anonapi.context import AnonAPIContext
from anonapi.decorators import pass_anonapi_context, handle_anonapi_exceptions
from anonapi.responses import JobStatus, JobInfoColumns, JobInfo, format_job_info_list
from collections import Counter

logger = logging.getLogger(__name__)


@click.group(name="batch")
def main():
    """Manage anonymization job batches"""
    pass


@click.command()
@pass_anonapi_context
@handle_anonapi_exceptions
def init(context: AnonAPIContext):
    """Save an empty batch in the current folder, for current server"""
    batch_folder = context.get_batch_folder()
    if batch_folder.has_batch():
        raise ClickException("Cannot init, A batch is already defined in this folder")
    else:
        server = context.get_active_server()
        batch_folder.save(JobBatch(job_ids=[], server=server))
        logger.info(f"Initialised batch for {server} in current dir")


@click.command()
@pass_anonapi_context
@handle_anonapi_exceptions
def info(context: AnonAPIContext):
    """Show batch in current directory"""
    logger.info(context.get_batch().to_string())


@click.command()
@pass_anonapi_context
@handle_anonapi_exceptions
def delete(context: AnonAPIContext):
    """Delete batch in current folder"""
    context.get_batch_folder().delete_batch()
    logger.info(f"Removed batch in current dir")


@click.command()
@pass_anonapi_context
@handle_anonapi_exceptions
@click.argument("job_ids", type=JobIDRangeParamType(), nargs=-1)
def add(context: AnonAPIContext, job_ids):
    """Add ids to current batch. Space-separated (1 2 3) or range (1-40)"""
    job_ids = [x for x in itertools.chain(*job_ids)]  # make into one list
    batch_folder: BatchFolder = context.get_batch_folder()
    batch: JobBatch = batch_folder.load()
    batch.job_ids = sorted(list(set(batch.job_ids) | set(job_ids)))
    batch_folder.save(batch)
    logger.info(f"Added {job_ids} to batch")


@click.command()
@pass_anonapi_context
@handle_anonapi_exceptions
@click.argument("job_ids", type=JobIDRangeParamType(), nargs=-1)
def remove(context: AnonAPIContext, job_ids):
    """Remove ids from current batch. Space-separated (1 2 3) or range (1-40)"""
    job_ids = [x for x in itertools.chain(*job_ids)]  # make into one list
    batch_folder = context.get_batch_folder()
    batch: JobBatch = batch_folder.load()
    batch.job_ids = sorted(list(set(batch.job_ids) - set(job_ids)))
    batch_folder.save(batch)

    logger.info(f"Removed {job_ids} from batch")


@click.command()
@pass_anonapi_context
@handle_anonapi_exceptions
@click.option(
    "--patient-name/--no-patient-name",
    default=False,
    help="Add pseudo patient id to command_table",
)
def status(context: AnonAPIContext, patient_name):
    """Print status overview for all jobs in batch"""

    batch = context.get_batch()

    if patient_name:
        get_extended_info = True
    else:
        get_extended_info = False

    ids_queried = batch.job_ids

    infos = context.client_tool.get_job_info_list(
        server=batch.server, job_ids=ids_queried, get_extended_info=get_extended_info,
    )

    logger.info(f"Job info for {len(infos)} jobs on {batch.server}:")
    columns_to_show = JobInfoColumns.DEFAULT_COLUMNS.copy()
    if patient_name:
        columns_to_show += [JobInfoColumns.pseudo_name]
    logger.info(infos.as_table_string(columns=columns_to_show))

    summary = ["Status       count   percentage", "-------------------------------"]
    status_count = Counter([x.status for x in infos])
    status_count["NOT_FOUND"] = len(ids_queried) - len(infos)
    for key, value in status_count.items():
        percentage = f"{(value / len(ids_queried) * 100):.1f} %"
        msg = f"{key:<12} {str(value):<8} {percentage:<8}"
        summary.append(msg)

    summary.append("-------------------------------")
    summary.append(f"Total        {str(len(ids_queried)):<8} 100%")

    logger.info(f"Summary for all {len(ids_queried)} jobs:")
    logger.info("\n".join(summary))


@click.command()
@pass_anonapi_context
@handle_anonapi_exceptions
def reset(context: AnonAPIContext):
    """Reset every job in the current batch"""
    batch: JobBatch = context.get_batch()

    if click.confirm(
        f"This will reset {len(batch.job_ids)} jobs on {batch.server}. Are you sure?"
    ):
        for job_id in batch.job_ids:
            logger.info(
                context.client_tool.reset_job(server=batch.server, job_id=job_id)
            )

        logger.info("Done")
    else:
        logger.info("User cancelled")


@click.command()
@pass_anonapi_context
@handle_anonapi_exceptions
def cancel(context: AnonAPIContext):
    """Cancel every job in the current batch"""
    batch: JobBatch = context.get_batch()

    if click.confirm(
        f"This will cancel {len(batch.job_ids)} jobs on {batch.server}. Are you sure?"
    ):
        for job_id in batch.job_ids:
            logger.info(
                context.client_tool.cancel_job(server=batch.server, job_id=job_id)
            )

        logger.info("Done")
    else:
        logger.info("User cancelled")


@click.command()
@pass_anonapi_context
@handle_anonapi_exceptions
def cancel_active(context: AnonAPIContext):
    """Cancel unprocessed (active) jobs, leave done and error"""
    batch: JobBatch = context.get_batch()

    infos = context.client_tool.get_job_info_list(
        server=batch.server, job_ids=batch.job_ids
    )

    job_ids = [x.job_id for x in infos if x.status == JobStatus.ACTIVE]

    if click.confirm(
        f"This will cancel {len(job_ids)} jobs on {batch.server}. Are you sure?"
    ):
        for job_id in job_ids:
            logger.info(
                context.client_tool.cancel_job(server=batch.server, job_id=job_id)
            )
        logger.info("Done")
    else:
        logger.info("User cancelled")


@click.command()
@pass_anonapi_context
@handle_anonapi_exceptions
def reset_error(context: AnonAPIContext):
    """Reset all jobs with error status in the current batch"""
    batch: JobBatch = context.get_batch()

    infos = context.client_tool.get_job_info_list(
        server=batch.server, job_ids=batch.job_ids
    )

    job_ids = [x.job_id for x in infos if x.status == JobStatus.ERROR]

    if click.confirm(
        f"This will reset {len(job_ids)} jobs on {batch.server}. Are you sure?"
    ):
        for job_id in job_ids:
            logger.info(
                context.client_tool.reset_job(server=batch.server, job_id=job_id)
            )

        logger.info("Done")
    else:
        logger.info("User cancelled")


@click.command()
@pass_anonapi_context
@handle_anonapi_exceptions
def show_error(context: AnonAPIContext):
    """Show full error message for all error jobs in batch"""
    batch: JobBatch = context.get_batch()

    infos = context.client_tool.get_job_info_list(
        server=batch.server, job_ids=batch.job_ids
    )

    error_infos: List[JobInfo] = [x for x in infos if x.status == JobStatus.ERROR]

    if error_infos:
        output = ""
        for info in error_infos:
            output += f"{format_job_info_list([info])}\n"
            output += "error message:\n"
            output += f"{info.error}\n\n"

        logger.info(output)
    else:
        logger.info("There are no jobs with error status in this batch")


for func in [
    info,
    status,
    reset,
    init,
    delete,
    add,
    remove,
    cancel,
    cancel_active,
    reset_error,
    show_error,
]:
    main.add_command(func)
