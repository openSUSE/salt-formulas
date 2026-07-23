import pytest


params_present = ['ontap.lun_present', 'name=testlun', 'comment="a present lun"', 'size=10MB', 'volume=myvol', 'vserver=mysvm']
state_present = 'ontap_|-testlun_|-testlun_|-lun_present'
params_mapped = ['ontap.lun_mapped', 'name=testlun', 'lunid=900', 'volume=myvol', 'vserver=mysvm', 'igroup=myigroup'] 
state_mapped = 'ontap_|-testlun_|-testlun_|-lun_mapped'
params_unmapped = ['ontap.lun_unmapped', 'name=testlun', 'volume=myvol', 'igroup=myigroup']
state_unmapped = 'ontap_|-testlun_|-testlun_|-lun_unmapped'


@pytest.mark.dependency(name='present')
@pytest.mark.parametrize('test', [True, False])
def test_lun_present(host, target, test):
    r = host.salt('state.single', params_present + [f'test={test}'])
    sr = r[state_present]
    assert sr['name'] == '/vol/myvol/testlun'
    if test:
        comment = 'Would provision LUN'
        result = None
    elif not test:
        comment = 'LUN /vol/myvol/testlun created with size 10MB.'
        result = True
    assert sr['comment'] == comment
    assert sr['result'] is result


@pytest.mark.dependency(depends=['present'], name='present_already')
@pytest.mark.parametrize('test', [True, False])
def test_lun_present_already(host, target, test):
    r = host.salt('state.single', params_present + [f'test={test}'])
    sr = r[state_present]
    assert sr['name'] == '/vol/myvol/testlun'
    assert sr['comment'] == 'LUN is already present; Size 10MB matches'
    assert sr['result'] is True


@pytest.mark.dependency(depends=['present_already'])
@pytest.mark.parametrize('test', [True, False])
def test_lun_present_resize(host, target, test):
    r = host.salt('state.single', ['ontap.lun_present', 'name=testlun', 'comment="a present lun"', 'size=20MB', 'volume=myvol', 'vserver=mysvm', f'test={test}'])
    sr = r[state_present]
    assert sr['name'] == '/vol/myvol/testlun'
    if test:
        comment = 'LUN is already present; Would resize LUN to 20MB'
        result = None
    elif not test:
        comment = 'LUN is already present; Successfully resized LUN from 10MB to 20MB'
        result = True
    assert sr['comment'] == comment
    assert sr['result'] is result


@pytest.mark.dependency(depends=['present_already'], name='mapped')
@pytest.mark.parametrize('test', [True, False])
def test_lun_mapped(host, target, test):
    r = host.salt('state.single', params_mapped + [f'test={test}'])
    sr = r[state_mapped]
    assert sr['name'] == '/vol/myvol/testlun'
    if test:
        comment = 'Would map ID 900 to igroup myigroup in SVM mysvm'
        result = None
    elif not test:
        comment = 'Mapped LUN to ID 900 in igroup myigroup'
        result = True
    assert sr['comment'] == comment
    assert sr['result'] is result


@pytest.mark.dependency(depends=['mapped'], name='mapped_already')
@pytest.mark.parametrize('test', [True, False])
def test_lun_mapped_already(host, target, test):
    r = host.salt('state.single', params_mapped + [f'test={test}'])
    sr = r[state_mapped]
    assert sr['name'] == '/vol/myvol/testlun'
    assert sr['comment'] == 'Already mapped to igroup myigroup in SVM mysvm'
    assert sr['result'] is True


@pytest.mark.dependency(depends=['mapped'], name='unmapped')
@pytest.mark.parametrize('test', [True, False])
def test_lun_unmapped(host, target, test):
    r = host.salt('state.single', params_unmapped + [f'test={test}'])
    sr = r[state_unmapped]
    assert sr['name'] == '/vol/myvol/testlun'
    if test:
        comment = 'Would unmap LUN'
        result = None
    elif not test:
        comment = 'Unmapped LUN'
        result = True
    assert sr['comment'] == comment
    assert sr['result'] is result


@pytest.mark.dependency(depends=['unmapped'], name='unmapped_already')
@pytest.mark.parametrize('test', [True, False])
def test_lun_unmapped_already(host, target, test):
    r = host.salt('state.single', params_unmapped + [f'test={test}'])
    sr = r[state_unmapped]
    assert sr['name'] == '/vol/myvol/testlun'
    assert sr['comment'] == 'Nothing to unmap'
    assert sr['result'] is True
