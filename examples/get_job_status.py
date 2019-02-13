from anonapi.client import WebAPIClient


def get_job_status():
    """Get information about a number of jobs

    """

    # Create a client that will talk to the web API
    client = WebAPIClient(
        hostname="https://umcradanonp11.umcn.nl/sandbox",
        username="z123sandbox",
        token="token",
    )

    # get the status for 3 specific jobs
    job_status_list = client.get("get_jobs_list", job_ids=[1, 2, 3])
    print(f"found status for {len(job_status_list)} jobs in list:")
    print(job_status_list)


if __name__ == "__main__":
    get_job_status()
