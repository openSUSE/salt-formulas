import os
import pytest
pytest.register_assert_rewrite('helpers')
from helpers import modes, vagenv, _vagrant



@pytest.fixture(scope='session')
def save():
    v = _vagrant()
    v.env = vagenv()
    v.snapshot_push()


@pytest.fixture()
def reset():
    v = _vagrant()
    v.env = vagenv()
    v.snapshot_pop()
    #v.destroy()
    #v.up()
    #ssh_config = v.ssh_config().replace('FATAL', 'VERBOSE')
    #with open('.scullery_ssh', 'w') as fh:
    #    fh.write(ssh_config)


@pytest.fixture(params=modes())
def mode(request):
    return request.param

