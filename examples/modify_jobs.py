from anonapi.client import WebAPIClient


def modify_jobs():
    """Modify several jobs

    Notes
    -----
    For a full list of the job fields that can be modified see example
    'get_api_definition'
    """

    # Create a client that will talk to the web API
    client = WebAPIClient(
        hostname="https://umcradanonp11.umcn.nl/sandbox",
        username="z123sandbox",
        token="token",
    )

    job_ids = [1, 2, 3]
    for job_id in job_ids:
        client.post(
            "modify_job",
            job_id=job_id,
            source_path=r"\\umcsanfsclp01\radng_imaging\temp\modified\test",
        )


if __name__ == "__main__":
    modify_jobs()
