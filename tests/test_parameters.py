import pytest

from anonapi.cli.create_commands import JobParameterSet
from anonapi.parameters import (SourceIdentifier, SourceIdentifierParameter,
                                Parameter, ParameterFactory, ParameterParsingError,
                                AccessionNumberIdentifier, StudyInstanceUIDIdentifier)
from tests.factories import SourceIdentifierParameterFactory


def test_source_identifier_parameter():
    """Slightly tricky parameter. source identifier is itself a complex object
    Should be usable like a simple object as a parameter"""

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


@pytest.mark.parametrize('identifier, expected_kwarg',
                         [(AccessionNumberIdentifier('1234567.12345678'),
                           'accession_number:1234567.12345678'), (
                          StudyInstanceUIDIdentifier('123.123.23'), '123.123.23')])
def test_parameter_as_kwargs(identifier, expected_kwarg):
    """This exposes a bug with accession numbers"""

    parameters = [
        SourceIdentifierParameter(identifier)]

    row = JobParameterSet(parameters=parameters)
    assert row.as_kwargs()['source_instance_id'] == expected_kwarg
