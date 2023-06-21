import dotenv
import json
import os
import vagrant

env = os.environ.copy()

def modes():
    # 'medium' removed -> FIXME results in error about fence_base being undefined ?
    # 'large' removed -> FIXME handle error about no defined STONITH resources
    # 'large_sbd' removed -> FIXME implement SBD simulation -> WIP
    return ['small', 'large_ipmi', 'large_ipmi_custom', 'large_sbd']

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


def setgrains(grains, host, target=None):
    for grainpair in grains:
        grain='test:{}'.format(grainpair[0])
        value=str(grainpair[1])
        if target is None:
            setgrain = host.salt('grains.set', [grain, value, 'force=True'])
        else:
            host.run(f'salt --out=json --static {target} grains.set {grain} {value} force=True').stdout


def vagenv():
    envmap = dotenv.dotenv_values('.scullery_env')
    for variable, value in envmap.items():
        env[variable] = value
    return env



def bootstrap_sbd(host):
    target='iqn.2003-01.org.linux-iscsi.scullery-master0.x8664:sn.5034edf18f27'
    initiators={'scullery-master0': 'iqn.1996-04.de.suse:01:3d33457f6212', 'scullery-minion0': 'iqn.1996-04.de.suse:01:dc7732f79cb2', 'scullery-minion1': 'iqn.1996-04.de.suse:01:35bb829ac08'}
    #with open('suse_ha-formula/tests/configs/target.json', 'r') as fh:
    #    config = fh.read()
    #run_config = host.run("echo '{}' > /etc/target/saveconfig.json && echo '{}' > /etc/iscsi/initiatorname.iscsi && mkdir /data/lun".format(config, initiators['scullery-master0']))
    #assert run_config.stdout == ''
    run_start = host.run("rctarget start && rctarget status")
    assert run_start.exit_status == 0
    assert 'status=0/SUCCESS' in run_start.stdout
    for client in ['scullery-minion0', 'scullery-minion1']:
        run_client = host.run("sudo salt --out=json --static {} cmd.run 'echo {} > /etc/iscsi/initiatorname.iscsi'".format(client, initiators[client]))
        print('run_client: '.format(str(run_client.stdout)))
    run_login = host.run("sudo salt --out=json --static \* cmd.run 'iscsiadm -m node -T {} -p scullery-master0 --login'".format(target))
    run_login_parsed = json.loads(run_login.stdout)
    print('run_login: '.format(str(run_login_parsed)))
    #assert run_login.stdout.startswith('Logging in to')
    assert run_login.exit_status == 0
    #assert run_login.stdout.endswith('successful.\n')
    run_scan = host.run("sudo salt --out=json --static \* cmd.run 'rescan-scsi-bus.sh'")
    run_scan_parsed = json.loads(run_scan.stdout)
    print('run_scan: '.format(str(run_scan_parsed)))
    assert run_scan.exit_status == 0

