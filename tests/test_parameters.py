from anonapi.parameters import SourceIdentifier, SourceIdentifierParameter


def test_source_identifier_parameter():
    """Slightly tricky parameter. source identifier is itself a complex object
    Should be usable like a simple object as a parameter"""

    assert str(SourceIdentifierParameter("folder:/test/kees")) \
           == 'source,folder:/test/kees'


