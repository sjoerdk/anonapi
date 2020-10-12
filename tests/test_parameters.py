import pytest

from anonapi.cli.create_commands import JobParameterSet
from anonapi.parameters import (
    PseudoID,
    SourceIdentifierParameter,
    ParameterFactory,
    ParameterParsingError,
    AccessionNumberIdentifier,
    StudyInstanceUIDIdentifier,
)


def test_source_identifier_parameter():
    """Slightly tricky parameter. source identifier is itself a complex object
    Should be usable like a simple object as a parameter
    """

    assert (
        str(SourceIdentifierParameter("folder:/test/kees"))
        == "source,folder:/test/kees"
    )


def test_parameter_factory():
    parsed = ParameterFactory.parse_from_string("pims_key,12345")
    assert parsed.value == "12345"
    assert parsed.field_name == "pims_key"

    # empty values should be possible
    assert not ParameterFactory.parse_from_string("pims_key,").value

    # tricky one. Should still work though
    parsed = ParameterFactory.parse_from_string(
        "source,folder:C:/windowsisgreat/folder"
    )
    assert parsed.field_name == "source"
    assert str(parsed.value) == "folder:C:/windowsisgreat/folder"


def test_parameter_factory_legacy_keys():
    """Legacy keys should be readable as parameter, but should yield their new
    parameter class so that load->save of any of these keys will update to the
    correct names
    """
    # patient_id should be parsed to the updated pseudo_id parameter
    parsed = ParameterFactory.parse_from_string("patient_id,12345")
    assert type(parsed) is PseudoID
    assert parsed.value == "12345"
    assert parsed.field_name == "pseudo_id"

    # this should be identical:
    parsed = ParameterFactory.parse_from_string("pseudo_id,12345")
    assert type(parsed) is PseudoID
    assert parsed.value == "12345"
    assert parsed.field_name == "pseudo_id"


@pytest.mark.parametrize(
    "input_string",
    [
        "pims_key",  # without comma
        "flims_key: 3434",  # unknown key
        "source,flolder:/tmp",  # unknown source type
    ],
)
def test_parameter_factory_exceptions(input_string):
    with pytest.raises(ParameterParsingError):
        ParameterFactory.parse_from_string(input_string)


@pytest.mark.parametrize(
    "identifier, expected_kwarg",
    [
        (
            AccessionNumberIdentifier("1234567.12345678"),
            "accession_number:1234567.12345678",
        ),
        (StudyInstanceUIDIdentifier("123.123.23"), "123.123.23"),
    ],
)
def test_parameter_as_kwargs(identifier, expected_kwarg):
    """Exposes a bug with accession numbers"""

    parameters = [SourceIdentifierParameter(identifier)]

    row = JobParameterSet(parameters=parameters)
    assert row.as_kwargs()["source_instance_id"] == expected_kwarg
