from anonapi.client import WebAPIClient


def cancel_job():
    """Create an IDIS job that pulls files from a network share

    """

    # Create a client that will talk to the web API
    client = WebAPIClient(
        hostname="https://umcradanonp11.umcn.nl/sandbox",
        username="z123sandbox",
        token="token",
    )

    # cancel job 100
    client.post("cancel_job", job_id=100)


if __name__ == "__main__":
    cancel_job()
