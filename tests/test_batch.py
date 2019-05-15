from io import StringIO

import pytest

from anonapi.batch import JobBatch
from anonapi.objects import RemoteAnonServer

@pytest.fixture()
def a_server():
    return RemoteAnonServer(name='temp', url='https://tempserver')


def test_batch_persisting(a_server):
    batch = JobBatch(job_ids=['1', '2', '3'], server=a_server)

    memfile = StringIO()
    batch.save(memfile)

    memfile.seek(0)
    loaded = JobBatch.load(memfile.getvalue())

    assert loaded.job_ids == batch.job_ids
    assert loaded.server.name == batch.server.name
    assert loaded.server.url == batch.server.url
