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


@pytest.mark.parametrize("human", [True, False])
def test_get_lun(host, target, lun, human):
    mycomment = lun['comment']
    myuuid = lun['uuid']
    myname = lun['name']
    r = host.salt('ontap.get_lun', ['a lonely lun', f'human={human}'])
    r0 = r[0]
    assert len(r0.keys()) == 5
    assert r0['comment'] == mycomment
    assert r0['name'] == myname
    if human:
        expsize = '10MB'
    elif not human:
        expsize = 10485760
    assert r0['space']['size'] == expsize
    assert r0['status']['mapped'] is False
    assert r0['uuid'] == myuuid


def test_map_lun(host, target, lun):
    myuuid = lun['uuid']
    mypath = lun['name']
    myvolume, myname = mypath.split('/')[2:]
    mysvm = lun['svm']['name']
    r = host.salt('ontap.map_lun', [myname, '900', myvolume, mysvm, 'myigroup'])
    assert r['result']
    assert r['status'] == 201
    result_rest = api(target, 'protocols/san/lun-maps', {'lun.uuid': myuuid})
    records = result_rest['records']
    r0 = records[0]
    assert r0['lun']['name'] == mypath


def test_get_lun_mapped(host, target, lun_mapped):
    lun = lun_mapped
    mypath = lun['name']
    mycomment = lun['comment']
    r = host.salt('ontap.get_lun_mapped', mycomment)
    assert r[mypath] is True


def test_get_lun_mapping(host, target, lun_mapped):
    lun = lun_mapped
    mysvm = lun['svm']['name']
    mypath = lun['name']
    myvolume, myname = mypath.split('/')[2:]
    r = host.salt('ontap.get_lun_mapping', [myname, myvolume, 'myigroup'])
    assert r['lun']['name'] == mypath
    assert r['svm']['name'] == mysvm


@pytest.mark.parametrize("igroup", [None, 'myigroup'])
def test_get_lun_mappings(host, target, lun_mapped, igroup):
    lun = lun_mapped
    mysvm = lun['svm']['name']
    mypath = lun['name']
    myvolume, myname = mypath.split('/')[2:]
    params = [myname, myvolume]
    if igroup is not None:
        params.append(igroup)
    r = host.salt('ontap.get_lun_mappings', params)
    assert len(r) == 1
    r0 = r[0]
    if igroup is not None:
        assert r0['igroup']['name'] == igroup
    assert r0['lun']['name'] == mypath
    assert r0['svm']['name'] == mysvm


def test_unmap_lun(host, target, lun_mapped):
    lun = lun_mapped
    mypath = lun['name']
    myvolume, myname = mypath.split('/')[2:]
    r = host.salt('ontap.unmap_lun', [myname, myvolume, 'myigroup'])
    assert r['result']
    assert r['status'] == 200


# to-do: test multiple unmappings
def test_unmap_luns(host, target, lun_mapped):
    lun = lun_mapped
    mypath = lun['name']
    myvolume, myname = mypath.split('/')[2:]
    r = host.salt('ontap.unmap_luns', [myname, myvolume, 'myigroup'])
    assert len(r) == 1
    r0 = r[0]
    assert r0['result']
    assert r0['status'] == 200
