import locale
from io import StringIO, TextIOWrapper
from pathlib import Path
from unittest.mock import Mock

import pytest
from fileselection.fileselection import FileSelectionFile

from anonapi.cli.map_commands import create_example_mapping
from anonapi.mapper import (
    JobParameterGrid,
    MapperException,
    MappingFile,
    MappingLoadError,
    Mapping,
    sniff_dialect,
)
from anonapi.parameters import (
    PathParameter,
    PseudoName,
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
    BASIC_MAPPING,
    BASIC_MAPPING_LOWER,
    BASIC_MAPPING_WITH_SPACE,
    COLON_SEPARATED_MAPPING,
    CAN_NOT_BE_PARSED_AS_MAPPING,
)

from tests.resources.test_mapper.example_sniffer_inputs import (
    BASIC_CSV_INPUT,
    SEPARATOR_LATE_IN_TEXT,
    VERY_SHORT_INPUT,
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


@pytest.fixture()
def a_mapping(a_grid_of_parameters):
    """A mapping containing 15 random lines"""
    return Mapping(grid=JobParameterGrid(rows=a_grid_of_parameters))


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
    mapping_file = RESOURCE_PATH / "test_mapper" / "example_job_grid.csv"
    with open(mapping_file, "r", newline="") as f:
        grid = JobParameterGrid.load(f)
    assert len(grid.rows) == 20


def test_job_parameter_grid_load_colon():
    mapping_file = RESOURCE_PATH / "test_mapper" / "example_job_grid_colon.csv"
    with open(mapping_file, "r", newline="") as f:
        grid = JobParameterGrid.load(f)
    assert len(grid.rows) == 4


def test_mapping_load_save():
    """Load file with CSV part and general part"""
    mapping_file = RESOURCE_PATH / "test_mapper" / "with_mapping_wide_settings.csv"
    with open(mapping_file, "r") as f:
        mapping = Mapping.load(f)
    assert "some comment" in mapping.description
    assert len(mapping.rows) == 20
    assert len(mapping.options) == 2

    output_file = StringIO(newline="")
    mapping.save_to(output_file)
    output_file.seek(0)
    loaded = Mapping.load(output_file)

    # saved and loaded again should be the same as original
    assert mapping.description == loaded.description
    assert [str(x) for x in mapping.options] == [str(x) for x in loaded.options]
    assert [str(param) for row in mapping.rows for param in row] == [
        str(param) for row in loaded.rows for param in row
    ]


@pytest.mark.parametrize(
    "content",
    [
        BASIC_MAPPING,
        BASIC_MAPPING_LOWER,
        COLON_SEPARATED_MAPPING,
        BASIC_MAPPING_WITH_SPACE,
    ],
)
def test_mapping_parse(content):
    """Content that can be parsed to a mapping"""

    stream = StringIO(initial_value=content)
    Mapping.load(stream)


@pytest.mark.parametrize("content", CAN_NOT_BE_PARSED_AS_MAPPING)
def test_mapping_parse_exceptions(content):
    """For these cases parsing should fail"""
    stream = StringIO(initial_value=content)
    with pytest.raises(MappingLoadError):
        _ = Mapping.parse_sections(stream)


def test_mapping_parse_colon_separated():
    """Excel in certain locales will save with colons. Make sure this works"""

    stream = StringIO(initial_value=COLON_SEPARATED_MAPPING)
    mapping = Mapping.load(stream)
    assert len(mapping.grid) == 4


def test_load_pims_only():
    mapping_file = RESOURCE_PATH / "test_mapper" / "example_pims_only_job_grid.csv"
    with open(mapping_file, "r") as f:
        JobParameterGrid.load(f)


@pytest.mark.parametrize(
    "file_to_open, expected_exception",
    [
        ("example_corrupt_job_grid.csv", MappingLoadError),
        ("example_job_grid_unknown_source_key.csv", MappingLoadError),
        ("example_job_grid_no_header.csv", MappingLoadError),
        ("example_job_grid_random_content.csv", MappingLoadError),
    ],
)
def test_load_exceptions(file_to_open, expected_exception):
    mapping_file = RESOURCE_PATH / "test_mapper" / file_to_open
    with pytest.raises(expected_exception):
        with open(mapping_file, "r") as f:
            JobParameterGrid.load(f)


def test_load_exception_contains_mapping_path():
    """Recreates issue #277. Stacktrace for load errors should list the mapping file
    path. This is very useful for debugging
    """

    mapping_file = MappingFile(
        file_path=RESOURCE_PATH / "test_mapper" / "example_corrupt_job_grid.csv"
    )

    with pytest.raises(MapperException) as e:
        mapping_file.get_mapping()
    assert str(mapping_file.file_path) in str(e)


def test_load_exception_missing_column_header():
    """Recreates issue #273. Missing a column header, a simple problem, causes a
    cryptic exception about parsing values with None and searching for commas
    """

    mapping_file = MappingFile(
        file_path=RESOURCE_PATH / "test_mapper" / "mapping_missing_column_header.csv"
    )

    with pytest.raises(MapperException) as e:
        mapping_file.get_mapping()
    assert "Missing column" in str(e.value)


def test_load_single_column_mapping():
    """Recreates issue #264. A Single column does not have separators. This
    caused a parse error. This should just work
    """

    mapping = MappingFile(
        file_path=RESOURCE_PATH / "test_mapper" / "mapping_single_column.csv"
    ).get_mapping()

    assert len(mapping.rows) == 2


def test_mapping_add_options():
    """Options in a mapping should be added to each row, unless overwritten by grid"""

    # two rows, one containing a pims key parameter
    a_grid = [
        [SourceIdentifierFactory(), PatientIDFactory(), PIMSKey("important!")],
        [SourceIdentifierFactory(), PatientIDFactory()],
    ]

    # mapping also defines a pims key as option
    mapping = Mapping(grid=JobParameterGrid(a_grid), options=[PIMSKey("GeneralKey")])

    rows = mapping.rows
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


def test_mapping_folder_read_write(tmpdir, a_grid_of_parameters):
    """Test creating reading and deleting mappings in folder"""

    # just some path
    path = tmpdir / "a_mapping.csv"
    assert not path.exists()

    # and an in-memory mapping
    mapping = Mapping(JobParameterGrid(a_grid_of_parameters))
    mapping_file = MappingFile(path)

    # when saving this to disk
    mapping_file.save_mapping(mapping)

    # the file should appear
    assert path.exists()

    # and content should be as expected
    assert [str(x) for row in mapping_file.load_mapping().rows for x in row] == [
        str(x) for row in mapping.rows for x in row
    ]


def test_os_error():
    with open(RESOURCE_PATH / "test_mapper" / "anon_mapping_os_error.csv", "r") as f:
        _ = Mapping.load(f)


def test_open_file():
    """Editors like openoffice and excel will lock open csv files. When combined
    with working on shares directly, the error messages can be quite confusing.
    No nice 'This file is opened in another application'. Make this slightly less
    confusing
    """

    mock = Mock(spec=TextIOWrapper)
    mock.__iter__ = Mock(
        side_effect=OSError(
            "raw readinto() returned invalid length 4294967283 "
            "(should have been between 0 and 8192)"
        )
    )

    with pytest.raises(MappingLoadError) as e:
        _ = Mapping.load(mock)

    assert "opened in any editor?" in str(e)


@pytest.mark.parametrize(
    "content, delimiter",
    [
        (BASIC_CSV_INPUT, ","),
        (COLON_SEPARATED_MAPPING, ";"),
        (SEPARATOR_LATE_IN_TEXT, ","),
        (VERY_SHORT_INPUT, ","),
    ],
)
def test_sniff_dialect(content, delimiter):
    """Find out whether this file has commas or colons as delimiters"""
    stream = StringIO(initial_value=content)
    dialect = sniff_dialect(stream)
    assert dialect.delimiter == delimiter


def test_sniff_dialect_exception():
    with pytest.raises(MapperException) as e:
        sniff_dialect(StringIO(initial_value="Just not a csv file."))
    assert "Could not determine dialect" in str(e)

    with pytest.raises(MapperException) as e:
        sniff_dialect(
            StringIO(initial_value="\n".join(["line1", "line2", "line3", "line4"]))
        )
    assert "Could not determine dialect" in str(e)


@pytest.mark.parametrize(
    "content, delimiter", [(BASIC_MAPPING, ","), (COLON_SEPARATED_MAPPING, ";")],
)
def test_read_write_dialect(content, delimiter):
    """The csv dialect in a mapping should not change when reading and writing"""

    temp_file = StringIO()
    mapping = Mapping.load(StringIO(initial_value=content))
    mapping.save_to(temp_file)
    temp_file.seek(0)
    assert sniff_dialect(temp_file).delimiter == delimiter
    temp_file.seek(0)
    Mapping.load(temp_file)  # Mapping should still be valid


@pytest.mark.parametrize(
    "locale_setting, delimiter", [(("nl_nl", "UTF8"), ";"), (("en_us", "UTF8"), ",")],
)
def test_write_new_mapping(monkeypatch, locale_setting, delimiter):
    """When writing a mapping from scratch, for example with 'map init', use
    the best guess at the current dialect and write csv files with comma or
    colon accordingly
    """
    with monkeypatch.context():
        locale.setlocale(locale.LC_ALL, locale_setting)
        temp_file = StringIO()
        create_example_mapping().save_to(temp_file)
        temp_file.seek(0)
        lines = temp_file.readlines()
        assert sniff_dialect(lines).delimiter == delimiter

        # Check that the correct delimiter is used in different parts of mapping
        assert sniff_dialect(lines[10:12]).delimiter == delimiter


def test_example_job_grid_save_correct_csv():
    """The initial mapping should be easily parsed as a csv. This means adding
    empty delimiters at the end of comments and section headers
    """
    temp_file = StringIO()
    create_example_mapping().save_to(temp_file)
    temp_file.seek(0)
    line = temp_file.readline()
    assert line


def test_cli_map_add_paths_file(a_mapping):
    """Add an xls file containing several paths and potentially pseudonyms
    to an existing mapping
    """

    assert len(a_mapping.grid) == 15

    grid = JobParameterGrid(
        rows=[
            [PathParameter(r"Kees\01"), PseudoName("Study1")],
            [PathParameter(r"Kees\02"), PseudoName("Study2")],
            [PathParameter(r"Henk\04"), PseudoName("Study3")],
        ]
    )

    a_mapping.add_grid(grid)

    assert len(a_mapping.grid) == 18
