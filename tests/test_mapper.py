from io import StringIO
from pathlib import Path
from unittest.mock import Mock

import pytest
from fileselection.fileselection import FileSelectionFile

from anonapi.mapper import (
    JobParameterGrid,
    MappingLoadError,
    MappingFolder,
    MapperException,
    Mapping,
)
from anonapi.parameters import (
    SourceIdentifierFactory,
    UnknownSourceIdentifierException,
    PIMSKey,
)
from tests.factories import (
    SourceIdentifierParameterFactory,
    PatientIDFactory,
    DescriptionFactory,
    PIMSKeyFactory,
)
from tests import RESOURCE_PATH
from tests.resources.test_mapper.example_mapping_inputs import (
    CAN_BE_PARSED_AS_MAPPING,
    CAN_NOT_BE_PARSED_AS_MAPPING,
)


@pytest.fixture()
def a_grid_of_parameters():
    """A grid of parameters that can be used to seed a JobParameterGrid

    Returns
    -------
    List[List[Parameter]]
    """

    def paramlist():
        return [
            SourceIdentifierParameterFactory(),
            PatientIDFactory(),
            DescriptionFactory(),
            PIMSKeyFactory(value=""),
        ]

    return [paramlist() for _ in range(15)]


def test_write(tmpdir, a_grid_of_parameters):
    mapping_list = JobParameterGrid(rows=a_grid_of_parameters)

    with open(Path(tmpdir) / "mapping.csv", "w") as f:
        mapping_list.save(f)

    with open(Path(tmpdir) / "mapping.csv", "r") as f:
        loaded_list = JobParameterGrid.load(f)

    # loaded should have the same patientIDs as the original
    for org, load in zip(mapping_list.rows, loaded_list.rows):
        assert [str(x) for x in org] == [str(x) for x in load]


def test_job_parameter_grid_load():
    mapping_file = RESOURCE_PATH / "test_mapper" / "example_mapping.csv"
    with open(mapping_file, "r", newline="") as f:
        grid = JobParameterGrid.load(f)
    assert len(grid.rows) == 20


def test_mapping_load_save():
    """Load file with CSV part and general part"""
    mapping_file = RESOURCE_PATH / "test_mapper" / "with_mapping_wide_settings.csv"
    with open(mapping_file, "r") as f:
        mapping = Mapping.load(f)
    assert "some comment" in mapping.description
    assert len(mapping.rows()) == 20
    assert len(mapping.options) == 2

    output_file = StringIO(newline="")
    mapping.save(output_file)
    output_file.seek(0)
    loaded = Mapping.load(output_file)

    # saved and loaded again should be the same as original
    assert mapping.description == loaded.description
    assert [str(x) for x in mapping.options] == [str(x) for x in loaded.options]
    assert [str(param) for row in mapping.rows() for param in row] == [
        str(param) for row in loaded.rows() for param in row
    ]


@pytest.mark.parametrize("content", CAN_BE_PARSED_AS_MAPPING)
def test_mapping_parse(content):
    """Parse into sections"""

    stream = StringIO(initial_value=content)
    parsed = Mapping.parse_sections(stream)
    assert len(parsed) == 3


@pytest.mark.parametrize("content", CAN_NOT_BE_PARSED_AS_MAPPING)
def test_mapping_parse_exceptions(content):
    """For  these cases parsing should fail"""
    stream = StringIO(initial_value=content)
    with pytest.raises(MappingLoadError):
        _ = Mapping.parse_sections(stream)


def test_load_pims_only():
    mapping_file = RESOURCE_PATH / "test_mapper" / "example_pims_only_mapping.csv"
    with open(mapping_file, "r") as f:
        mapping = JobParameterGrid.load(f)


@pytest.mark.parametrize(
    "file_to_open, expected_exception",
    [
        ("example_corrupt_mapping.csv", MappingLoadError),
        ("example_unknown_source_key.csv", MappingLoadError),
        ("example_mapping_no_header.csv", MappingLoadError),
        ("example_mapping_random_content.csv", MappingLoadError),
    ],
)
def test_load_exceptions(file_to_open, expected_exception):
    mapping_file = RESOURCE_PATH / "test_mapper" / file_to_open
    with pytest.raises(expected_exception) as e:
        with open(mapping_file, "r") as f:
            JobParameterGrid.load(f)


def test_mapping_add_options():
    """Options in a mapping should be added to each row, unless overwritten by
    grid"""

    # two rows, one containing a pims key parameter
    a_grid = [
        [SourceIdentifierFactory(), PatientIDFactory(), PIMSKey("important!")],
        [SourceIdentifierFactory(), PatientIDFactory()],
    ]

    # mapping also defines a pims key as option
    mapping = Mapping(grid=JobParameterGrid(a_grid), options=[PIMSKey("GeneralKey")])

    rows = mapping.rows()
    assert rows[0][0].value == "important!"
    assert rows[1][0].value == "GeneralKey"


def test_source_identifier_factory():
    factory = SourceIdentifierFactory()
    assert (
        factory.get_source_identifier_for_key("folder:/something/folder").key
        == "folder"
    )
    assert factory.get_source_identifier_for_key("base:123234").key == "base"

    for faulty_key in ["somethingelse:123234", "folder,123234", "folder123234"]:
        with pytest.raises(UnknownSourceIdentifierException):
            factory.get_source_identifier_for_key(faulty_key)


def test_source_identifier_factory_object_to_identifier():
    factory = SourceIdentifierFactory()
    identifier = factory.get_source_identifier_for_obj(
        FileSelectionFile(
            data_file_path="testpath/folder/datafile.txt", description="test"
        )
    )

    assert str(identifier) == "fileselection:testpath/folder/datafile.txt"


def test_format_job_info(a_grid_of_parameters):
    grid = JobParameterGrid(rows=a_grid_of_parameters)
    as_string = grid.to_table_string()

    assert "with 15 rows" in as_string


def test_mapping_list_folder():
    with_mapping = MappingFolder(
        RESOURCE_PATH / "test_mapper" / "mapping_list_folder" / "with_mapping"
    )
    without_mapping = MappingFolder(
        RESOURCE_PATH / "test_mapper" / "mapping_list_folder" / "without_mapping"
    )
    assert with_mapping.has_mapping()
    assert not without_mapping.has_mapping()


def test_mapping_list_folder_path_funcs():
    path = RESOURCE_PATH / "test_mapper" / "mapping_list_folder" / "with_mapping"
    assert str(MappingFolder(path).make_relative(path / "foo/bar")) == "foo/bar"
    assert (
        str(MappingFolder(path).make_relative("already/relative")) == "already/relative"
    )

    with pytest.raises(MapperException):
        MappingFolder(path).make_relative("/outside/scope")

    assert MappingFolder(path).make_absolute("foo/bar") == path / "foo/bar"

    with pytest.raises(MapperException):
        MappingFolder(path).make_absolute("/absolute/root_path")


def test_mapping_folder_read_write(tmpdir, a_grid_of_parameters):
    """Test creating reading and deleting mappings in folder"""
    mapping_folder = MappingFolder(tmpdir)
    assert not mapping_folder.has_mapping()

    mapping = Mapping(JobParameterGrid(a_grid_of_parameters))
    mapping_folder.save_mapping(mapping)
    assert mapping_folder.has_mapping()

    loaded = mapping_folder.load_mapping()
    assert [str(x) for row in loaded.rows() for x in row] == [
        str(x) for row in mapping.rows() for x in row
    ]
    assert mapping_folder.has_mapping()

    mapping_folder.delete_mapping()
    assert not mapping_folder.has_mapping()


def test_os_error():
    with open(RESOURCE_PATH / "test_mapper" / "anon_mapping_os_error.csv", "r") as f:
        _ = Mapping.load(f)


def test_open_file():
    """Editors like openoffice and excel will lock open csv files. When combined
    with working on shares directly, the error messages can be quite confusing.
    No nice 'This file is opened in another application'. Make this slightly less
    confusing
    """

    mapping_file = RESOURCE_PATH / "test_mapper" / "with_mapping_wide_settings.csv"
    with open(mapping_file, "r") as f:
        f.readlines = Mock(
            side_effect=OSError(
                "raw readinto() returned invalid length 4294967283 "
                "(should have been between 0 and 8192)"
            )
        )
        with pytest.raises(MappingLoadError) as e:

            _ = Mapping.load(f)

        assert "opened in any editor?" in str(e)
