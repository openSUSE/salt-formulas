from lib import api
import json
import pytest


@pytest.mark.dependency(name='provision')
def test_lun_provision(host, target):
    r = host.salt('ontap.provision_lun', ['provisiontestlun', '10MB', 'myvol', 'mysvm', 'a provisioned lun'])
    assert r['result']
    assert r['status'] == 201
    result_rest = api(target, 'storage/luns', {'fields': 'comment,space.size'})
    records = result_rest['records']
    for entry, record in enumerate(records):
        if record['name'] == '/vol/myvol/provisiontestlun':
            myrecord = records[entry]
            break
    assert myrecord, 'Did not find any record matching the created LUN name'
    assert myrecord['name'] == '/vol/myvol/provisiontestlun'
    assert myrecord['comment'] == 'a provisioned lun'
    assert myrecord['space']['size'] == 10485760


@pytest.mark.dependency(depends=['provision'])
def test_lun_delete_name(host, target):
    r = host.salt('ontap.delete_lun_name', ['provisiontestlun', 'myvol'])
    assert r['result']
    assert r['status'] == 200
    result_rest = api(target, 'storage/luns', {'fields': 'comment,space.size'})
    records = result_rest['records']
    assert not '/vol/myvol/provisiontestlun' in records


def test_lun_delete_uuid(host, target, lun):
    myuuid = lun['uuid']
    r = host.salt('ontap.delete_lun_uuid', myuuid)
    assert r['result']
    assert r['status'] == 200
    result_rest = api(target, 'storage/luns')
    records = result_rest['records']
    assert not any(record['uuid'] == myuuid for record in records)


def test_lun_resize(host, target, lun):
    myuuid = lun['uuid']
    r = host.salt('ontap.update_lun', [myuuid, '20MB'])
    assert r['result']
    assert r['status'] == 200
    result_rest = api(target, 'storage/luns', {'fields': 'space.size'})
    records = result_rest['records']
    for entry, record in enumerate(records):
        if record['name'] == '/vol/myvol/testlun':
            myrecord = records[entry]
            break
    assert myrecord, 'Did not find any record matching the created LUN name'
    assert myrecord['space']['size'] == 20971520


def test_lun_resize_reduce_fail(host, target, lun):
    myuuid = lun['uuid']
    r = host.run_expect([1], f'salt-call --out=json ontap.update_lun {myuuid} 5MB')
    rout = json.loads(r.stdout)['local']
    assert not rout['result']
    assert rout['status'] == 400
    assert rout['message'] == 'Reducing the size of a LUN might cause permanent data loss or corruption and is not supported by the LUN REST API. The ONTAP command "lun resize" can be used to reduce the LUN size.'
    result_rest = api(target, 'storage/luns', {'fields': 'space.size'})
    records = result_rest['records']
    for entry, record in enumerate(records):
        if record['name'] == '/vol/myvol/testlun':
            myrecord = records[entry]
            break
    assert myrecord, 'Did not find any record matching the created LUN name'
    assert myrecord['space']['size'] == 10485760
