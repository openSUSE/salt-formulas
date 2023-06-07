import pytest
import yaml

@pytest.fixture
def file():
    return '/etc/salt/grains'

def test_grains_file_exists(host, file):
    with host.sudo():
        exists = host.file(file).exists
    assert exists is True

def test_grains_file_contents(host, file):
    with host.sudo():
        struct = host.file(file).content.decode('UTF-8')
    data = yaml.safe_load(struct)
    assert data['snack'] == 'peanuts' and data['treats'][0] == 'chocolate'

def test_grains_file_ownership(host, file):
    with host.sudo():
        user = host.file(file).user
    assert user == 'root'

def test_grains_salt(host, file):
    with host.sudo():
        snack = host.salt('grains.get', 'snack', local=True)
    assert snack == 'peanuts'
