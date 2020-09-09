"""Example .csv file contents for sniffing the type of csv"""

BASIC_CSV_INPUT = r"""
destination_path,\\someserver\share\folder1
pims_key,555
"""

# After saving in excel with a locale with colon list separator.
# Tricky things here are colons and the empty lines with ;;; content
COLON_SEPARATED = r"""
source;patient_id;patient_name;description
folder:example\folder1;1;Patient1;All files from folder1
study_instance_uid:123.12121212.12345678;2;Patient2;A study which should be retrieved from PACS, identified by StudyInstanceUID
accession_number:12345678.1234567;3;Patient3;A study which should be retrieved from PACS, identified by AccessionNumber
fileselection:folder2\fileselection.txt;4;Patient4;A selection of files in folder2
"""

# When sniffing only the start of a file you might miss any comma
SEPARATOR_LATE_IN_TEXT = r"""
A lot of text but actually no comma. Which should be fine, 1
"""

# This might cause a problem when reading too far?
VERY_SHORT_INPUT = r"""
test1,10
test2,20
"""

# This should give a reasonable error
NOT_CSV = r"""
This is just a text. Not a csv file.
"""
