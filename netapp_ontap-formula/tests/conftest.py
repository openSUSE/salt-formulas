from lib import api
import pytest

@pytest.fixture
def target():
    # FIXME make this configurable
    return '10.168.0.97'

@pytest.fixture
def lun(host, target):
    r = host.salt('ontap.provision_lun', ['testlun', '10MB', 'myvol', 'mysvm', 'a lonely lun'])
    assert r['result']
    assert r['status'] == 201
    r_prequery =  api(target, 'storage/luns')
    records_pre = r_prequery['records']
    for entry, record in enumerate(records_pre):
        if record['name'] == '/vol/myvol/testlun':
            myrecord = records_pre[entry]
    assert myrecord, 'Did not find any record matching the created LUN fixture name'
    myuuid = myrecord['uuid']
    assert any(record['uuid'] == myuuid for record in records_pre), 'LUN fixture does not show in records'

    yield myrecord

    r_midquery = api(target, 'storage/luns')
    records_mid = r_midquery['records']
    for entry, record in enumerate(records_mid):
        if record['name'] == '/vol/myvol/testlun':
            myuuid = records_mid[entry]['uuid']
            # probably better to delete using a direct API call here in case there is a problem with delete_lun_uuid
            r = host.salt('ontap.delete_lun_uuid', myuuid)
            assert r['result']
            assert r['status'] == 200

    r_finquery = api(target, 'storage/luns')
    records_fin = r_finquery['records']
    assert not any(record['uuid'] == myuuid for record in records_fin), 'Failed to clean up LUN fixture'
