from pathlib import Path

import pytest

from anonapi.mapper import MappingList, SourceIdentifierFactory, UnknownSourceIdentifier, AnonymizationParameters, \
    MappingLoadError
from tests.factories import AnonymizationParametersFactory, FileSelectionIdentifierFactory
from tests import RESOURCE_PATH


def test_write(tmpdir):
    mapping = {FileSelectionIdentifierFactory(): AnonymizationParametersFactory() for _ in range(20)}
    mapping_list = MappingList(mapping=mapping)
    with open(Path(tmpdir) / 'mapping.csv', 'w') as f:
        mapping_list.save(f)


def test_anonymization_parameters():
    params = AnonymizationParameters(patient_id='pat1', patient_name='name1', description='desc')
    assert params.as_dict()['patient_id'] == 'pat1'

    subset = params.as_dict(parameters_to_include=[AnonymizationParameters.PATIENT_NAME])
    assert 'patient_id' not in subset
    assert subset['patient_name'] == 'name1'


def test_load():
    mapping_file = RESOURCE_PATH / 'test_mapper' / 'example_mapping.csv'
    with open(mapping_file, 'r') as f:
        mapping = MappingList.load(f)
    assert len(mapping) == 20


@pytest.mark.parametrize('file_to_open, expected_exception',
                         [('example_corrupt_mapping.csv', UnknownSourceIdentifier),
                          ('example_unknown_source_key.csv', UnknownSourceIdentifier),
                          ('example_mapping_no_header.csv', MappingLoadError)
                          ])
def test_load_exceptions(file_to_open, expected_exception):
    mapping_file = RESOURCE_PATH / 'test_mapper' / file_to_open
    with pytest.raises(expected_exception) as e:
        with open(mapping_file, 'r') as f:
            MappingList.load(f)


def test_source_identifier_factory():
    factory = SourceIdentifierFactory()
    assert factory.get_source_identifier("folder:/something/folder").key == 'folder'
    assert factory.get_source_identifier("base:123234").key == 'base'

    for faulty_key in ["somethingelse:123234", "folder::123234", "folder123234"]:
        with pytest.raises(UnknownSourceIdentifier):
            factory.get_source_identifier(faulty_key)


def test_write_subset(tmpdir):
    """Write only certain anonymization parameters. This makes the generated csv simpler
    """
    mapping = {FileSelectionIdentifierFactory(): AnonymizationParametersFactory() for _ in range(20)}
    mapping_list = MappingList(mapping=mapping)

    mapfile = Path(tmpdir) / 'mapping.csv'
    with open(mapfile, 'w') as f:
        mapping_list.save(f, parameters_to_write=[AnonymizationParameters.PATIENT_ID_NAME])

    # when loading this file again, the parameters that were not written should be missing
    with open(mapfile, 'r') as f:
        loaded = MappingList.load(f)

    for identifier, parameters in loaded.items():
        assert str(identifier) in map(str, mapping.keys())  # all original values should have been saved
        assert loaded[identifier].patient_id is not None
        assert loaded[identifier].patient_name is None
        assert loaded[identifier].description is None


def test_write_subset_unknown_parameter(tmpdir):
    """Try to constrain to a parameter that is not a valid anonymization parameter
    """
    mapping = {FileSelectionIdentifierFactory(): AnonymizationParametersFactory() for _ in range(20)}
    mapping_list = MappingList(mapping=mapping)

    with pytest.raises(ValueError):
        with open(Path(tmpdir) / 'mapping.csv', 'w') as f:
            mapping_list.save(f, parameters_to_write=['Whatisthis'])
