from lib import api

def test_lun_provision(host, target):
    r = host.salt('ontap.provision_lun', ['testlun', '10MB', 'myvol', 'mysvm', 'a lonely lun'])
    assert r['result']
    assert r['status'] == 201
    result_rest = api(target, 'storage/luns', {'fields': 'comment,space.size'})
    records = result_rest['records']
    for entry, record in enumerate(records):
        if record['name'] == '/vol/myvol/testlun':
            myrecord = records[entry]
            break
    assert myrecord, 'Did not find any record matching the created LUN name'
    assert myrecord['name'] == '/vol/myvol/testlun'
    assert myrecord['comment'] == 'a lonely lun'
    assert myrecord['space']['size'] == 10485760
