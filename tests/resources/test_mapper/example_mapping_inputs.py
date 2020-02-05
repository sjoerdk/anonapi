"""
Example .csv file contents that should be parsable as a mapping, or should fail
Used in test_mapping.
"""

CAN_BE_PARSED_AS_MAPPING = [
    r"""
## Description ##
some comment by some person        
## Options ##
destination_path,\\someserver\share\folder1
pims_key,555        
## Mapping ##
source,patient_id,patient_name,description
folder:/folder/file0,patient0,patientName0,test description        
""",
    # Lower case titles should not matter
    r"""  
## description ##
some comment by some person        
## options ##
destination_path,\\someserver\share\folder1
pims_key,555        
## Mapping ##
source,patient_id,patient_name,description
folder:/folder/file0,patient0,patientName0,test description        
""",
]


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
