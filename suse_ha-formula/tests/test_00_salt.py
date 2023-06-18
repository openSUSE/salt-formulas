import copy
import dotenv
import json
import os
import pytest
import re
import vagrant
import testinfra
#testinfra_hosts = ['scullery-minion0', 'scullery-minion1', 'scullery-master0']

env = os.environ.copy()

def _vagrant():
    return vagrant.Vagrant(quiet_stderr=False)

# https://stackoverflow.com/a/9808122
def find(key, value):
  for k, v in value.items():
    if k == key:
      yield v
    elif isinstance(v, dict):
      for result in find(key, v):
        yield result
    elif isinstance(v, list):
      for d in v:
        for result in find(key, d):
          yield result


def find_changes(result, count=False):
    found = find('changes', result)
    changed = False
    counter = 0
    for change in list(found):
        if change:
            changed = True
            if count is False:
                break
            count += 1
    if count is False:
        return changed
    return changed, counter


def setgrains(grains, host):
    for grainpair in grains:
        grain='test:{}'.format(grainpair[0])
        value=str(grainpair[1])
        setgrain = host.salt('grains.set', [grain, value, 'force=True'])


@pytest.fixture(scope='session')
def reset():
    v = _vagrant()
    envmap = dotenv.dotenv_values('.scullery_env')
    for variable, value in envmap.items():
        env[variable] = value
    v.env = env
    v.destroy()
    v.up()
    ssh_config = v.ssh_config()
    with open('.scullery_ssh', 'w') as fh:
        fh.write(ssh_config)


def modes():
    # 'medium' removed -> FIXME results in error about undefined fence_base being undefined ?
    # 'large' removed -> FIXME handle error about no defined STONITH resources
    return ['small', 'large_ipmi', 'large_ipmi_custom', 'large_sbd']


@pytest.fixture(params=modes())
def mode(request):
    return request.param


def grainsdata(grainmode):
    if grainmode == 'small':
        testgrains = [('with_fencing', False), ('with_stonith', False), ('with_ipmi', False), ('with_sbd', False), ('with_ipmi_custom', False)]
    if grainmode == 'medium':
        testgrains = [('with_fencing', True), ('with_stonith', False), ('with_ipmi', False), ('with_sbd', False), ('with_ipmi_custom', False)]
    if grainmode == 'large':
        testgrains = [('with_fencing', True), ('with_stonith', True), ('with_ipmi', False), ('with_sbd', False), ('with_ipmi_custom', False)]
    if grainmode == 'large_ipmi':
        testgrains = [('with_fencing', True), ('with_stonith', True), ('with_ipmi', True), ('with_sbd', False), ('with_ipmi_custom', False)]
    if grainmode == 'large_ipmi_custom':
        testgrains = [('with_fencing', True), ('with_stonith', True), ('with_ipmi', True), ('with_sbd', False), ('with_ipmi_custom', True)]
    if grainmode == 'large_sbd':
        testgrains = [('with_fencing', True), ('with_stonith', True), ('with_ipmi', False), ('with_sbd', True), ('with_ipmi_custom', False)]

    return testgrains


def pillardata(pillarmode, host):
    addresses = json.loads(host.run('ip --json a sh eth0').stdout)[0]['addr_info']
    for address in addresses:
        if address['family'] == 'inet':
            bind_address = address['local']
            break

    # FIXME: instead of duplicating the test pillar data here, read, render and merge the local SLS files

    if pillarmode == 'small':
        testpillar = {'suse_ha': {'cluster': {'nodeid': 2, 'name': 'scullery'}, 'multicast': {'bind_address': bind_address}, 'resources_dir': '/data/resources'}}

    elif pillarmode == 'large':
        testpillar = {'suse_ha': {'cluster': {'nodeid': 2, 'name': 'scullery'}, 'multicast': {'bind_address': bind_address}, 'resources_dir': '/data/resources', 'fencing': {'stonith_enable': True}}}

    elif pillarmode == 'large_ipmi':
        testpillar = {'suse_ha': {'cluster': {'nodeid': 2, 'name': 'scullery'}, 'multicast': {'bind_address': bind_address}, 'resources_dir': '/data/resources', 'fencing': {'stonith_enable': True, 'ipmi': {'hosts': {'dev-ipmi0': {'ip': '192.168.120.1', 'port': 60010, 'user': 'admin', 'interface': 'lanplus', 'priv': 'ADMINISTRATOR', 'secret': 'password'}, 'dev-ipmi1': {'ip': '192.168.120.1', 'port': 60011, 'user': 'admin', 'interface': 'lanplus', 'priv': 'ADMINISTRATOR', 'secret': 'password'}}}}}}

    elif pillarmode == 'large_ipmi_custom':
        # FIXME: somehow allow for configurable IPMI IP addresses
        testpillar = {'suse_ha': {'cluster': {'nodeid': 2, 'name': 'scullery'}, 'multicast': {'bind_address': bind_address}, 'resources_dir': '/data/resources', 'fencing': {'stonith_enable': True, 'ipmi': {'primitive': {'operations': {'start': {'timeout': 30}}}, 'hosts': {'dev-ipmi0': {'ip': '192.168.120.1', 'port': 60010, 'user': 'admin', 'interface': 'lanplus', 'priv': 'ADMINISTRATOR', 'secret': 'password'}, 'dev-ipmi1': {'ip': '192.168.120.1', 'port': 60011, 'user': 'admin', 'interface': 'lanplus', 'priv': 'ADMINISTRATOR', 'secret': 'password'}}}}}}

    elif pillarmode == 'large_sbd':
        testpillar = {'suse_ha': {'cluster': {'nodeid': 2, 'name': 'scullery'}, 'multicast': {'bind_address': bind_address}, 'resources_dir': '/data/resources', 'fencing': {'stonith_enable': True, 'sbd': {'instances': {'minion0': {'pcmk_host_list': 'minion0', 'pcmk_delay_base': 0}, 'minion1': {'pcmk_host_list': 'minion1', 'pcmk_delay_base': 0}, 'dynamic': {'pcmk_delay_max': 5}}, 'devices': ['/dev/sda', '/dev/sdb', '/dev/sdc']}}}}

    else:
        testpillar = {}

    return testpillar


def test_salt_grains(host, mode):
    mygrains = grainsdata(mode)
    setgrains(mygrains, host)
    grainsout = host.salt('grains.item', 'test')

    grains = {'test': {}}
    for grainpair in mygrains:
        grains['test'].update({grainpair[0]: grainpair[1]})

    assert grains.items() <= grainsout.items()


def test_salt_pillar(host, mode):
    setgrains(grainsdata(mode), host)

    result = host.salt('pillar.item', 'suse_ha')

    assert pillardata(mode, host) == result


def test_salt_state_show_sls(host, mode):
    setgrains(grainsdata(mode), host)

    result = host.salt('state.show_sls', 'suse_ha')

    assert result


expectations_state_apply_test_common = {
            'pkg_|-suse_ha_packages_|-suse_ha_packages_|-installed': {
                'comment': 'The following packages would be installed/updated: chrony, conntrack-tools, corosync, crmsh, ctdb, fence-agents, ldirectord, pacemaker, python3-python-dateutil, resource-agents, virt-top'
            },
            'file_|-/etc/corosync/corosync.conf_|-/etc/corosync/corosync.conf_|-managed': {
                'comment': 'The file /etc/corosync/corosync.conf is set to be changed\nNote: No changes made, actual changes may\nbe different due to other states.'
            },
            'file_|-/etc/corosync/authkey_|-/etc/corosync/authkey_|-managed': {
                'comment': 'The file /etc/corosync/authkey is set to be changed\nNote: No changes made, actual changes may\nbe different due to other states.'
            },
            'service_|-corosync.service_|-corosync.service_|-running': {
                'comment': 'Service is set to be started'
            },
            'file_|-pacemaker.service_|-/etc/sysconfig/pacemaker_|-keyvalue': {
                'comment': 'unable to open /etc/sysconfig/pacemaker'
            },
            'service_|-pacemaker.service_|-pacemaker.service_|-running': {
                'comment': 'Service pacemaker.service not present; if created in this state run, it would have been started  The state would be retried every 10 seconds (with a splay of up to 5 seconds) a maximum of 3 times or until a result of True is returned'
            },
}
expectations_state_apply_test_moded = {
        'small': {},
        'large': {},
        'large_ipmi': {
            'file_|-ha_fencing_ipmi_secret_dev-ipmi0_|-/etc/pacemaker/ha_ipmi_dev-ipmi0_|-managed': {
                'comment': 'The file /etc/pacemaker/ha_ipmi_dev-ipmi0 is set to be changed\nNote: No changes made, actual changes may\nbe different due to other states.'
            },
            'file_|-ha_fencing_ipmi_secret_dev-ipmi1_|-/etc/pacemaker/ha_ipmi_dev-ipmi1_|-managed': {
                'comment': 'The file /etc/pacemaker/ha_ipmi_dev-ipmi1 is set to be changed\nNote: No changes made, actual changes may\nbe different due to other states.'
            },
        },
        'large_ipmi_custom': {
            'file_|-ha_fencing_ipmi_secret_dev-ipmi0_|-/etc/pacemaker/ha_ipmi_dev-ipmi0_|-managed': {
                'comment': 'The file /etc/pacemaker/ha_ipmi_dev-ipmi0 is set to be changed\nNote: No changes made, actual changes may\nbe different due to other states.'
            },
            'file_|-ha_fencing_ipmi_secret_dev-ipmi1_|-/etc/pacemaker/ha_ipmi_dev-ipmi1_|-managed': {
                'comment': 'The file /etc/pacemaker/ha_ipmi_dev-ipmi1 is set to be changed\nNote: No changes made, actual changes may\nbe different due to other states.'
            },
        },
        'large_sbd': {
            'pkg_|-suse_ha_packages_|-suse_ha_packages_|-installed': {
                'comment': 'The following packages would be installed/updated: chrony, conntrack-tools, corosync, crmsh, ctdb, fence-agents, ldirectord, pacemaker, python3-python-dateutil, resource-agents, virt-top, sbd'
            },
            'file_|-sbd_sysconfig_|-/etc/sysconfig/sbd_|-keyvalue': {
                'comment': 'unable to open /etc/sysconfig/sbd'
            },
            # the following three are not right ; reference the whitelist comment below
            'service_|-sbd_service_|-sbd_|-enabled': {
                'comment': 'The named service sbd is not available'
            },
            'service_|-corosync.service_|-corosync.service_|-running': {
                'comment': 'One or more requisite failed: suse_ha.sbd.sbd_service'
            },
            'service_|-pacemaker.service_|-pacemaker.service_|-running': {
                'comment': 'One or more requisite failed: suse_ha.corosync.corosync.service'
            },
        },
}
expectations_state_apply_test_params = [
        pytest.param(m, expectations_state_apply_test_moded[m])
        for m in modes()
]
@pytest.mark.parametrize('mode, expected', expectations_state_apply_test_params)
def test_salt_state_apply_test(host, mode, expected):
    setgrains(grainsdata(mode), host)

    print('mode: ' + mode)

    result = host.salt('state.apply', ['suse_ha', 'test=True'], expect_rc=[0, 1])

    with open('/dev/shm/result_{}'.format(mode), 'w', encoding='utf-8') as fh:
        json.dump(result, fh, ensure_ascii=False, indent=4)

    changed = find_changes(result)
    assert changed

    result = result['local']
    expected_moderesults = copy.deepcopy(expectations_state_apply_test_common)
    expected_moderesults.update(expected)

    for state, body in result.items():
        print(state)
        fields = body.keys()
        assert 'comment' in fields, 'States must return a comment'
        assert 'result' in fields, 'States must return a result'
        assert state in expected_moderesults, 'States must be tracked in test suite'
        # https://github.com/saltstack/salt/pull/62259
        whitelist = r'^service_\|-\w+[_\.]\w+_\|-\w+(?:\.\w+)?_\|-(?:enabled|running)$'
        if not re.match(whitelist, state):
            assert body['result'] is not False
        for field in fields:
            if field in expected_moderesults[state]:
                assert body[field] == expected_moderesults[state][field]

    # FIXME: assert expected dict length

    #print('changed: ' + str(changed))
    #print('changes: ' + str(changes))


expectations_state_apply_common = {
            'pkg_|-suse_ha_packages_|-suse_ha_packages_|-installed': {
                'comment': '11 targeted packages were installed/updated.'
            },
            'file_|-ha_resources_directory_|-/data/resources_|-directory': {
                'comment': ''
            },
            'file_|-/etc/corosync/corosync.conf_|-/etc/corosync/corosync.conf_|-managed': {
                'comment': 'File /etc/corosync/corosync.conf updated'
            },
            'file_|-/etc/corosync/authkey_|-/etc/corosync/authkey_|-managed': {
                'comment': 'File /etc/corosync/authkey updated'
            },
            'service_|-corosync.service_|-corosync.service_|-running': {
                'comment': 'Service corosync.service is already disabled, and is running'
            },
            'file_|-pacemaker.service_|-/etc/sysconfig/pacemaker_|-keyvalue': {
                'comment': ''
            },
            'service_|-pacemaker.service_|-pacemaker.service_|-running': {
                'comment': 'Service pacemaker.service has been enabled, and is running'
            },
}
expectations_state_apply_moded = {
        'small': {},
        'large': {},
        'large_ipmi': {
            'file_|-ha_fencing_ipmi_secret_dev-ipmi0_|-/etc/pacemaker/ha_ipmi_dev-ipmi0_|-managed': {
                'comment': ''
            },
            'file_|-ha_fencing_ipmi_secret_dev-ipmi1_|-/etc/pacemaker/ha_ipmi_dev-ipmi1_|-managed': {
                'comment': ''
            },
        },
        'large_ipmi_custom': {
            'file_|-ha_fencing_ipmi_secret_dev-ipmi0_|-/etc/pacemaker/ha_ipmi_dev-ipmi0_|-managed': {
                'comment': ''
            },
            'file_|-ha_fencing_ipmi_secret_dev-ipmi1_|-/etc/pacemaker/ha_ipmi_dev-ipmi1_|-managed': {
                'comment': ''
            },
        },
        'large_sbd': {
            'pkg_|-suse_ha_packages_|-suse_ha_packages_|-installed': {
                'comment': '12 targeted packages were installed/updated.'
            },
            'file_|-sbd_sysconfig_|-/etc/sysconfig/sbd_|-keyvalue': {
                'comment': ''
            },
            'service_|-sbd_service_|-sbd_|-enabled': {
                'comment': ''
            },
            'service_|-corosync.service_|-corosync.service_|-running': {
                'comment': ''
            },
            'service_|-pacemaker.service_|-pacemaker.service_|-running': {
                'comment': ''
            },
        },
}
expectations_state_apply_params = [
        pytest.param(m, expectations_state_apply_moded[m])
        for m in modes()
]
host_params = [
        pytest.param(h)
        for h in testinfra.get_hosts(['scullery-minion0', 'scullery-minion1'], ssh_config='.scullery_ssh', sudo=True)
]
@pytest.mark.parametrize('minion', host_params)
@pytest.mark.parametrize('mode, expected', expectations_state_apply_params)
def test_salt_state_apply(minion, mode, expected, reset):
    print('mode: ' + mode)
    setgrains(grainsdata(mode), minion)

    minion.salt('saltutil.refresh_pillar')
    minion.salt('mine.update')

    # the first time the state applied Corosync might not be ready, and fail to start
    # to-do: add some sort of "wait for readiness" logic to the formula
    #result0 = host.salt('state.apply', 'suse_ha', expect_rc=[1])
    result0 = minion.salt('state.apply', 'suse_ha')
    with open('/dev/shm/result0_{}'.format(mode), 'w', encoding='utf-8') as fh:
        json.dump(result0, fh, ensure_ascii=False, indent=4)

    #host.salt('mine.update')

    #try:
    #    result1 = host.salt('state.apply', 'suse_ha')
    #except Exception:
    #    pass
    #with open('/dev/shm/result1_{}'.format(mode), 'w', encoding='utf-8') as fh:
    #    json.dump(result1, fh, ensure_ascii=False, indent=4)
    # well maybe one result is good enough now??
    result = result0

    changed, changes = find_changes(result, True)
    assert changed
    print('changes: ' + str(changes))

    #result = host.salt('state.apply', 'suse_ha')
    #assert result
    #changed = find_changes(result)
    #assert not changed

    #result = result['local']
    expected_moderesults = copy.deepcopy(expectations_state_apply_common)
    expected_moderesults.update(expected)

    for state, body in result.items():
        print(state)
        fields = body.keys()
        assert 'comment' in fields, 'States must return a comment'
        assert 'result' in fields, 'States must return a result'
        assert state in expected_moderesults, 'States must be tracked in test suite'
        assert body['result'] is not False
        # FIXME
        for field in fields:
            if field in expected_moderesults[state]:
                assert body[field] == expected_moderesults[state][field]

