from anonapi.client import WebAPIClient


def anonymize_files_from_idc():
    """Create an IDIS job that pulls files from the hospital information system"""

    # Create a client that will talk to the web API
    client = WebAPIClient(
        hostname="https://umcradanonp11.umcn.nl/sandbox",
        username="z123sandbox",
        token="token",
    )

    # Create a job that takes data from the IDC (formally IMPAX) directly
    anon_name = "TEST_NAME_02"
    anon_id = "02"
    sid = "123.12335.3353.36464.343435677"  # study UID
    destination_path = r"\\umcsanfsclp01\radng_imaging\temptest_output"
    idc_job_info = client.post(
        "create_job",
        source_type="WADO",
        source_name="IDC_WADO",
        source_instance_id=sid,
        anonymizedpatientname=anon_name,
        anonymizedpatientid=anon_id,
        destination_type="PATH",
        project_name="Wetenschap-Algemeen",
        destination_path=destination_path,
        description=f"A test idc job",
    )
    print(f"Succesfully created a job in {client}, job_id={idc_job_info['job_id']}")


if __name__ == "__main__":
    anonymize_files_from_idc()
