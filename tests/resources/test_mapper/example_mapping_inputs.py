"""
Example .csv file contents that should be parsable as a mapping, or should fail
Used in test_mapping.
"""

BASIC_MAPPING = r"""
## DESCRIPTION ##,,,
some comment by some person,,,
,,,,
## OPTIONS ##,,,
destination_path,\\someserver\share\folder1,,
pims_key,555,,
## MAPPING ##,,,
source,patient_id,patient_name,description
folder:/folder/file0,patient0,patientName0,test description
"""

# Lower case titles should not matter
BASIC_MAPPING_LOWER = r"""
## description ##,,,
some comment by some person,,,
,,,,
## options ##,,,
destination_path,\\someserver\share\folder1,,
pims_key,555,,
## Mapping ##,,,
source,patient_id,patient_name,description
folder:/folder/file0,patient0,patientName0,test description
"""

# After saving in excel with a locale with colon list separator.
# Tricky things here are colons and the empty lines with ;;; content
COLON_SEPARATED_MAPPING = r"""
## Description ##;;;
Mapping created September 09 2020 by user;;;
;;;
## Options ##;;;
root_source_path;C:\temp;;
project;Wetenschap-Algemeen;;
destination_path;\\server\share\folder;;
;;;
## Mapping ##;;;
source;patient_id;patient_name;description
folder:example\folder1;1;Patient1;All files from folder1
study_instance_uid:123.12121212.12345678;2;Patient2;A study which should be retrieved from PACS, identified by StudyInstanceUID
accession_number:12345678.1234567;3;Patient3;A study which should be retrieved from PACS, identified by AccessionNumber
fileselection:folder2\fileselection.txt;4;Patient4;A selection of files in folder2
"""


CAN_NOT_BE_PARSED_AS_MAPPING = [
    # Missing description
    r"""## Options ##
destination_path,\\someserver\share\folder1
pims_key,555
## Mapping ##
source,patient_id,patient_name,description
folder:/folder/file0,patient0,patientName0,test description
""",
    # mistyped description
    r"""
## Desc ##
some comment by some person
## options ##
destination_path,\\someserver\share\folder1
pims_key,555
## Mapping ##
source,patient_id,patient_name,description
folder:/folder/file0,patient0,patientName0,test description
""",
]
# Recreates #327, space on empty line under options will yield unneeded exception
BASIC_MAPPING_WITH_SPACE = r"""
## DESCRIPTION ##,,,
Has a space under options. This recreates #327,,,
,,,,
## OPTIONS ##,,,
 ,,,
destination_path,\\someserver\share\folder1,,
pims_key,555,,
## MAPPING ##,,,
source,patient_id,patient_name,description
folder:/folder/file0,patient0,patientName0,test description
"""
