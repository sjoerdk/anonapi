from anonapi.client import WebAPIClient


def anonymize_files_from_share():
    """Create an IDIS job that pulls files from a network share"""

    # Create a client that will talk to the web API
    client = WebAPIClient(
        hostname="https://umcradanonp11.umcn.nl/sandbox",
        username="z123sandbox",
        token="token",
    )

    # Create a job that takes data from a source on a network root_path, and writes
    # the anonymized data to a destination that is also a network root_path. Note
    # that the network root_path should be accessible for the anonymization server
    # for this to work.
    anon_name = "TEST_NAME_01"
    anon_id = "01"
    source_path = r"\\umcsanfsclp01\radng_imaging\temp\test"
    destination_path = r"\\umcsanfsclp01\radng_imaging\temptest_output"
    network_job_info = client.post(
        "create_job",
        source_type="PATH",
        source_path=source_path,
        destination_type="PATH",
        project_name="Wetenschap-Algemeen",
        destination_path=destination_path,
        anonymizedpatientname=anon_name,
        anonymizedpatientid=anon_id,
        description=f"A test root_path job",
    )
    # new_job_info response contains extended info on the new job that has just been created
    print(f"Succesfully created a job in {client}, job_id={network_job_info['job_id']}")


if __name__ == "__main__":
    anonymize_files_from_share()
