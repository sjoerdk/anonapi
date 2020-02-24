class RequestMockResponse:
    """A description of a http server response
    """

    def __init__(self, text, response_code):
        """

        Parameters
        ----------
        text: str
            Text of this response
        response_code: int
            https response code, like 200 or 404
        """

        self.text = text
        self.response_code = response_code


class RequestsMockResponseExamples:
    """Some examples of http response texts that an anonymization web API server
     might send back. Harvested and simplified these from a live API server
     running git revision 9c36082e3dafab5fac0fb9d34963970493b20776 in diag repo

    To use these in an external test:


    """

    API_CALL_NOT_DEFINED = (
        r'{"404": "The API call you tried to make is not defined, here is some documentation", '
        r'"documentation":{"overview":"some docs"}}'
    )

    JOBS_LIST_GET_JOBS = (
        '{"1": {"job_id": 1, "date": "2018-10-26T14:56:34", "user_name": "z123sandbox", "status":'
        ' "INACTIVE", "error": null, "description": null, "project_name": "Wetenschap-Algemeen", "priority": 0,'
        ' "files_downloaded": null, "files_processed": null}, "2": {"job_id": 2, '
        '"date": "2018-09-19T11:16:57", "user_name": "z123sandbox", "status": "ACTIVE", "error": null,'
        ' "description": "For RSNA2018. see ticket #1672", "project_name": "ProCAD", "priority": 0,'
        ' "files_downloaded": null, "files_processed": null}}'
    )  # Response to 'get_jobs'

    JOBS_LIST_GET_JOBS_LIST = (
        '{"1000": {"job_id": 1000, "date": "2016-08-26T15:04:44", "user_name": "Z495159", '
        '"status": "DONE", "error": null, "description": null, "project_name": "testproject", "priority": 1,'
        ' "files_downloaded": 0, "files_processed": 0}, "1002": {"job_id": 1002, "date": "2016-08-26T15:04:44",'
        ' "user_name": "Z495159", "status": "UPLOADED", "error": null, "description": null, '
        '"project_name": "testproject", "priority": 1, "files_downloaded": 0, "files_processed": 0},'
        ' "5000": {"job_id": 5000, "date": "2016-09-23T20:46:51", "user_name": "Z495159", "status": '
        '"UPLOADED", "error": null, "description": null, "project_name": "testproject", "priority": 1,'
        ' "files_downloaded": 3, "files_processed": 3}}'
    )  # Response to 'get_jobs_list'

    JOBS_LIST_GET_JOBS_EXTENDED = (
        '{"1001": {"job_id": 1001, "date": "2019-11-26T16:34:07", "user_name": '
        '"z428172", "status": "DONE", "error": " ", "description": "For ticket '
        '#8941", "project_name": "Wetenschap-Algemeen", "priority": 0, "files'
        '_downloaded": 11, "files_processed": 11, "destination_id": 53767, '
        '"destination_name": null, "destination_path": '
        '"\\\\\\\\umcsanfsclp01\\\\radng_axti\\\\datasets\\\\CoffeeBreak\\\\Coffeebreak'
        '_newrecons", "destination_network": null, "destination_status": "BASE",'
        ' "destination_type": "PATH", "source_id": 53767, "source_instance_id":'
        ' null, "source_status": "NEW", "source_type": "PATH", "source_'
        'anonymizedpatientid": "1982", "source_anonymizedpatientname": "1982", '
        '"source_pims_keyfile_id": null, "source_name": null, "source_path": '
        '"fileselection:\\\\\\\\umcsanfsclp01\\\\radng_ctarchive\\\\clinical_'
        'archive\\\\0677380\\\\fileselection.txt", "source_protocol": 3178, '
        '"source_subject": 3178}, "1002": {"job_id": 1002, "date": '
        '"2019-11-26T16:34:08", "user_name": "z428172", "status": "DONE",'
        ' "error": null, "description": "For ticket #8941", "project_name": '
        '"Wetenschap-Algemeen", "priority": 0, "files_downloaded": 11, '
        '"files_processed": 11, "destination_id": 1002, "destination_name": null, '
        '"destination_path": "\\\\\\\\umcsanfsclp01\\\\radng_axti\\\\datasets'
        '\\\\CoffeeBreak\\\\Coffeebreak_newrecons", "destination_network": '
        'null, "destination_status": "BASE", "destination_type": "PATH", "source'
        '_id": 1002, "source_instance_id": null, "source_status": "NEW", "source'
        '_type": "PATH", "source_anonymizedpatientid": "1983", "source_'
        'anonymizedpatientname": "1983", "source_pims_keyfile_id": null, '
        '"source_name": null, "source_path": "fileselection:\\\\\\\\umcsanfsclp0'
        "1\\\\radng_ctarchive\\\\clinical_archive\\\\5187581\\\\fileselection."
        'txt", "source_protocol": 3178, "source_subject": 3178}, "1003": '
        '{"job_id": 1003, "date": "2019-11-26T16:34:08", "user_name": "z428172", '
        '"status": "DONE", "error": " ", "description": "For ticket #8941",'
        ' "project_name": "Wetenschap-Algemeen", "priority": 0, '
        '"files_downloaded": 11, "files_processed": 11, "destination_id": 1001,'
        ' "destination_name": null, "destination_path": "\\\\\\\\umcsanfsclp01'
        '\\\\radng_axti\\\\datasets\\\\CoffeeBreak\\\\Coffeebreak_newrecons", '
        '"destination_network": null, "destination_status": "BASE", "destination'
        '_type": "PATH", "source_id": 1001, "source_instance_id": null, '
        '"source_status": "NEW", "source_type": "PATH", "source_anonymizedpatientid":'
        ' "1984", "source_anonymizedpatientname": "1984", "source_pims_keyfile_'
        'id": null, "source_name": null, "source_path": "fileselection:\\\\\\\\'
        "umcsanfsclp01\\\\radng_ctarchive\\\\clinical_archive\\\\0572800\\\\"
        'fileselection.txt", "source_protocol": 3178, "source_subject": 3178}}'
    )  # Response to 'get_jobs_list_extended'

    JOBS_LIST_GET_JOBS_LIST_WITH_ERROR = (
        '{"1": {"job_id": 1, "date": "2016-08-26T15:04:44", "user_name": "Z495159", '
        '"status": "ERROR", "error": "Something wrong", "description": null, "project_name": "testproject", '
        '"priority": 1, "files_downloaded": 0, "files_processed": 0}, "2": {"job_id": 2, "date": "2016-08-26T15:04:44",'
        ' "user_name": "Z495159", "status": "UPLOADED", "error": null, "description": null, '
        '"project_name": "testproject", "priority": 1, "files_downloaded": 0, "files_processed": 0},'
        ' "3": {"job_id": 3, "date": "2016-09-23T20:46:51", "user_name": "Z495159", "status": '
        '"ERROR", "error": "Terrible error", "description": null, "project_name": "testproject", "priority": 1,'
        ' "files_downloaded": 3, "files_processed": 3}}'
    )  # Response to 'get_jobs_list'

    JOB_INFO = (
        r'{"job_id": 3, "date": "2018-08-31T11:11:05", "user_name": "z123sandbox", "status": "INACTIVE",'
        r' "error": null, "description": null, "project_name": "Wetenschap-Algemeen", "priority": 10,'
        r' "files_downloaded": null, "files_processed": null, "destination_id": 44777, '
        r'"destination_name": null, "destination_path": "\\\\resfilsp10\\imaging\\temp\\test_output",'
        r' "destination_network": null, "destination_status": "BASE", "destination_type": "PATH",'
        r' "source_id": 44777, "source_instance_id": null, "source_status": "NEW", "source_type": "PATH",'
        r' "source_anonymizedpatientid": null, "source_anonymizedpatientname": null, "source_name": null,'
        r' "source_path": "f", "source_protocol": 3178, "source_subject": 3178}'
    )

    JOB_CREATED_RESPONSE = RequestMockResponse(
        r'{"job_id": 1234, "date": "2019-09-04T14:12:43", "user_name": "z123sandbox", '
        r'"status": "ACTIVE", "error": null, "description": "A test root_path job", '
        r'"project_name": "Wetenschap-Algemeen", "priority": 0, "files_downloaded": null, '
        r'"files_processed": null, "destination_id": 44806, "destination_name": null,'
        r' "destination_path": "\\\\umcsanfsclp01\\radng_imaging\\temptest_output",'
        r' "destination_network": null, "destination_status": "BASE", "destination_type": "PATH",'
        r' "source_id": 44806, "source_instance_id": null, "source_status": "NEW",'
        r' "source_type": "PATH", "source_anonymizedpatientid": "01",'
        r' "source_anonymizedpatientname": "TEST_NAME_01", "source_name": null,'
        r' "source_path": "\\\\umcsanfsclp01\\radng_imaging\\temp\\test", '
        r'"source_protocol": 3178, "source_subject": 3178}',
        200,
    )

    JOB_DOES_NOT_EXIST = r'{"errors": {"job_id": "Job with id 447783 does not exist"}}'

    ERROR_USER_NOT_CONNECTED_TO_PROJECT = RequestMockResponse(
        r'{"errors": {"AnonymizeInputException": "given user_'
        r"name `test_changed` is not connected to given project"
        r'_name testproject"}}',
        400,
    )

    REQUIRED_PARAMETER_NOT_SUPPLIED = (
        r'{"errors": {"job_id": "Required parameter job_id not supplied"}}'
    )


