from pathlib import Path

import pytest

from anonapi.paths import UNCPath, UNCMapping, UNCMap, UNCMappingException


@pytest.mark.parametrize(
    "path",
    [
        "//server/share/thing",
        Path(r"\\server\share\thing"),
        r"//server/share/thing\weirdpath_3467#&^f" r"\\server\share\thing",
        r"\\server\share",
        "//server/share/thing",
    ],
)
def test_unc_path(path):
    """All these paths should be accepted as valid unc paths"""
    UNCPath(path)


@pytest.mark.parametrize(
    "path",
    [
        "/server/share/thing",
        r"/server/share/thing\weirdpath_3467#&^f",
        r"//server",
        Path(r"\server\share\thing"),
        r"\\server",
        "C:/yomomma",
    ],
)
def test_unc_path(path):
    """All these paths should be rejected"""
    with pytest.raises(ValueError):
        UNCPath(path)


def test_unc_mapping():

    local1 = Path("/mnt/thatshare")
    unc1 = UNCPath(r"\\server\thatshare")
    local2 = Path("/mnt/othershare")
    unc2 = UNCPath(r"\\server\thatothershare")

    mapping = UNCMapping(
        maps=[UNCMap(local=local1, unc=unc1), UNCMap(local=local2, unc=unc2)]
    )

    a_local_path = local1 / 'folder1' / 'a_file.txt'

    # converting to unc and back again should not change the path
    unc = mapping.to_unc(a_local_path)
    local = mapping.to_local(UNCPath(unc))
    assert local == a_local_path

    # converting already converted should not be a problem
    assert local == mapping.to_local(local)

    unc = mapping.to_unc(a_local_path)
    assert unc == mapping.to_unc(unc)

    # unknown paths will still work if conversion is not needed
    unknown_path = Path('/not_known')
    assert mapping.to_local(unknown_path) == unknown_path
    unknown_share = Path(r'\\an_unknown_server\share\file.txt')
    assert mapping.to_unc(unknown_share) == unknown_share

    # but if conversion *is* needed, unknown paths will raise
    with pytest.raises(UNCMappingException):
        mapping.to_local(unknown_share)

    with pytest.raises(UNCMappingException):
        mapping.to_unc(unknown_path)




