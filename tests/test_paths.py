from pathlib import Path

import pytest

from anonapi.paths import UNCPath, UNCMapping, UNCMap


@pytest.mark.parametrize('path',
                         ['//server/share/thing',
                          Path(r'\\server\share\thing'),
                          r'//server/share/thing\weirdpath_3467#&^f'
                          r'\\server\share\thing',
                          r'\\server\share',
                          '//server/share/thing',
                          ])
def test_unc_path(path):
    """All these paths should be accepted as valid unc paths"""
    UNCPath(path)


@pytest.mark.parametrize('path',
                         ['/server/share/thing',
                          r'/server/share/thing\weirdpath_3467#&^f',
                          r'//server',
                          Path(r'\server\share\thing'),
                          r'\\server',
                          'C:/yomomma',
                          ])
def test_unc_path(path):
    """All these paths should be rejected"""
    with pytest.raises(ValueError):
        UNCPath(path)


def test_unc_mapping():
    mapping = UNCMapping(
        mapping=[UNCMap(local=Path("/mnt/thatshare"),
                        unc=UNCPath(r'\\server\thatshare')),
                 UNCMap(local=Path("/mnt/othershare"),
                        unc=UNCPath(r'\\server\thatothershare'))
                 ])

    unc = mapping.to_unc(Path('/mnt/thatshare/folder1/a_file.txt'))
    test = 1