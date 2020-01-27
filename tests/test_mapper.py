from pathlib import Path

import pytest
from fileselection.fileselection import FileSelectionFile

from anonapi.mapper import (MappingList, SourceIdentifierFactory,
                            UnknownSourceIdentifier, AnonymizationParameters,
                            MappingLoadError, MappingListFolder, MapperException)
from tests.factories import (
    AnonymizationParametersFactory,
    FileSelectionIdentifierFactory,
)
from tests import RESOURCE_PATH


@pytest.fixture()
def a_mapping():
    return {
        FileSelectionIdentifierFactory(): AnonymizationParametersFactory()
        for _ in range(20)
    }


def test_write(tmpdir, a_mapping):
    mapping_list = MappingList(mapping=a_mapping)
    with open(Path(tmpdir) / "mapping.csv", "w") as f:
        mapping_list.save(f)

    with open(Path(tmpdir) / "mapping.csv", "r") as f:
        loaded_list = MappingList.load(f)

    # loaded should have the same patientIDs as the original
    all(
        y.patient_id in [x.patient_id for x in a_mapping.values()]
        for y in loaded_list.values()
    )


def test_anonymization_parameters():
    params = AnonymizationParameters(
        patient_id="pat1", patient_name="name1", description="desc"
    )
    assert params.as_dict()["patient_id"] == "pat1"

    subset = params.as_dict(
        parameters_to_include=[AnonymizationParameters.PATIENT_NAME]
    )
    assert "patient_id" not in subset
    assert subset["patient_name"] == "name1"


def test_load():
    mapping_file = RESOURCE_PATH / "test_mapper" / "example_mapping.csv"
    with open(mapping_file, "r") as f:
        mapping = MappingList.load(f)
    assert len(mapping) == 20


def test_load_pims_only():
    mapping_file = RESOURCE_PATH / "test_mapper" / "example_pims_only_mapping.csv"
    with open(mapping_file, "r") as f:
        mapping = MappingList.load(f)
    test = 1


@pytest.mark.parametrize(
    "file_to_open, expected_exception",
    [
        ("example_corrupt_mapping.csv", UnknownSourceIdentifier),
        ("example_unknown_source_key.csv", UnknownSourceIdentifier),
        ("example_mapping_no_header.csv", MappingLoadError),
        ("example_mapping_random_content.csv", MappingLoadError),
    ],
)
def test_load_exceptions(file_to_open, expected_exception):
    mapping_file = RESOURCE_PATH / "test_mapper" / file_to_open
    with pytest.raises(expected_exception) as e:
        with open(mapping_file, "r") as f:
            MappingList.load(f)


def test_source_identifier_factory():
    factory = SourceIdentifierFactory()
    assert factory.get_source_identifier_for_key("folder:/something/folder").key == "folder"
    assert factory.get_source_identifier_for_key("base:123234").key == "base"

    for faulty_key in ["somethingelse:123234", "folder::123234", "folder123234"]:
        with pytest.raises(UnknownSourceIdentifier):
            factory.get_source_identifier_for_key(faulty_key)


def test_source_identifier_factory_object_to_identifier():
    factory = SourceIdentifierFactory()
    identifier = factory.get_source_identifier_for_obj(
        FileSelectionFile(data_file_path='testpath/folder/datafile.txt',
                          description='test'))

    assert str(identifier) == 'fileselection:testpath/folder/datafile.txt'


def test_write_subset(tmpdir, a_mapping):
    """Write only certain anonymization parameters. This makes the generated csv simpler
    """
    mapping_list = MappingList(mapping=a_mapping)

    mapfile = Path(tmpdir) / "mapping.csv"
    with open(mapfile, "w") as f:
        mapping_list.save(
            f, parameters_to_write=[AnonymizationParameters.PATIENT_ID_NAME]
        )

    # when loading this file again, the parameters that were not written should be missing
    with open(mapfile, "r") as f:
        loaded = MappingList.load(f)

    for identifier, parameters in loaded.items():
        assert str(identifier) in map(
            str, a_mapping.keys()
        )  # all original values should have been saved
        assert loaded[identifier].patient_id is not None
        assert loaded[identifier].patient_name is None
        assert loaded[identifier].description is None


def test_write_subset_unknown_parameter(tmpdir, a_mapping):
    """Try to constrain to a parameter that is not a valid anonymization parameter
    """
    mapping_list = MappingList(mapping=a_mapping)

    with pytest.raises(ValueError):
        with open(Path(tmpdir) / "mapping.csv", "w") as f:
            mapping_list.save(f, parameters_to_write=["Whatisthis"])


def test_format_job_info(a_mapping):
    mapping_list = MappingList(mapping=a_mapping)
    as_string = mapping_list.to_table_string()

    assert "Mapping with 20 entries" in as_string
    assert all(str(x) in as_string for x in list(mapping_list))


def test_mapping_list_folder():
    with_mapping = MappingListFolder(
        RESOURCE_PATH / "test_mapper" / "mapping_list_folder" / "with_mapping"
    )
    without_mapping = MappingListFolder(
        RESOURCE_PATH / "test_mapper" / "mapping_list_folder" / "without_mapping"
    )
    assert with_mapping.has_mapping_list()
    assert not without_mapping.has_mapping_list()


def test_mapping_list_folder_path_funcs():
    path = RESOURCE_PATH / "test_mapper" / "mapping_list_folder" / "with_mapping"
    assert str(MappingListFolder(path).make_relative(path / "foo/bar")) == "foo/bar"
    assert str(MappingListFolder(path).make_relative("already/relative")
               ) == "already/relative"

    with pytest.raises(MapperException):
        MappingListFolder(path).make_relative("/outside/scope")

    assert MappingListFolder(path).make_absolute("foo/bar") == path / "foo/bar"

    with pytest.raises(MapperException):
        MappingListFolder(path).make_absolute("/absolute/path")


def test_mapping_folder_read_write(tmpdir, a_mapping):
    """Test creating reading and deleting mappings in folder"""
    mapping_folder = MappingListFolder(tmpdir)
    assert not mapping_folder.has_mapping_list()

    mapping_list = MappingList(a_mapping)
    mapping_folder.save_list(mapping_list)
    assert mapping_folder.has_mapping_list()

    loaded = mapping_folder.load_list()
    assert set(map(str, a_mapping)) == set(map(str, loaded))
    assert mapping_folder.has_mapping_list()

    mapping_folder.delete_list()
    assert not mapping_folder.has_mapping_list()
