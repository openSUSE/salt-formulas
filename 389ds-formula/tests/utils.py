"""
Helpers for testing of the 389-DS formula
Copyright (C) 2026 SUSE LLC <georg.pfuetzenreuter@suse.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from json import loads
from shlex import join

import pytest

# name of 389ds instance and backend suffix to test against
INSTANCE = 'testidm'
SUFFIX = 'dc=example,dc=com'
PASS = '{PBKDF2-SHA512}25000$N4bwPickZMz5v5cyJkQIIQ$PQojDC.8pY/DWOU1XDnwwglQmRyk671j3MpYRMI1Thv494pajOunezf9IAiTlQEJSJ9Y5iMR06UJQvPk.kj6MQ'

DSCONF_FILE = '/root/.389_testidm.inf'

def cmd(args):
    return join(args)

def cmd_dsconf(args):
    return cmd(['sudo', 'dsconf'] + args)

def instance_setup(host, samples=False):
    with open('389ds-formula/tests/dsconf.inf') as fh:
        dsconf = fh.read()

    result = host.run(cmd(['sudo', 'zypper', '-nq', 'in', '389-ds']))
    if result.rc != 0:
        pytest.fail('Could not install 389-ds for testing.')

    if samples:
        dsconf = dsconf + 'sample_entries = yes\n'

    dsconf = dsconf + '\n\n'

    result = host.run(f"printf '{dsconf}' | sudo tee {DSCONF_FILE}")
    if result.rc != 0:
        pytest.fail('Could not write dsconf for testing.')

    host.run(cmd(['sudo', 'chmod', '0600', DSCONF_FILE]))

    result = host.run(cmd(['sudo', 'dscreate', 'from-file', DSCONF_FILE]))
    if result.rc != 0:
        pytest.fail('Could not create testing instance.')

    result = host.run(cmd(['sudo', 'systemctl', 'start', f'dirsrv@{INSTANCE}']))
    if result.rc != 0:
        pytest.fail('Could not start testing instance.')

    if samples:
        result = host.run(cmd_dsconf([INSTANCE, 'replication', 'enable', '--suffix', SUFFIX, '--role', 'supplier', '--replica-id', str(1), '--bind-dn', 'cn=replication manager,cn=config', '--bind-passwd', 'foo']))
        if result.rc != 0:
            pytest.fail('Could not create replication for testing.')


def instance_teardown(host):
    result = host.run(cmd(['sudo', 'dsctl', INSTANCE, 'remove', '--do-it']))
    if result.rc != 0:
        print('Could not delete testing instance.')

    result = host.run(cmd(['sudo', 'zypper', '-nq', 'rm', '389-ds']))
    if result.rc != 0:
        print('Could not remove 389-ds for testing.')

    result = host.run(cmd(['sudo', 'rm', DSCONF_FILE]))


def salt(host, command):
    print(command)
    result = host.run(f'sudo salt-call --local --out json {command}')
    print(result)

    output = loads(result.stdout)['local']

    # JSON only knows arrays and Salt CLI converts tuple returns to lists; convert those back to make assertions less confusing to match with tested functions
    if isinstance(output, list) and len(output) == 2:
        output = tuple(output)

    return output, result.stderr, result.rc


def reduce_state_out(data):
    out = {}

    for state, subdata in data.items():
        tmp = {}
        for k, v in subdata.items():
            if k in ['changes', 'comment', 'name', 'result']:
                tmp[k] = v
        out[state] = dict(sorted(tmp.items()))

    return out


def expand_expect_out(data, test):
    out = {}

    for state, subdata in data.items():
        out[state] = {}

        for k in ['changes', 'comment', 'name', 'result']:
            if k in subdata:
                v = subdata[k]
                if isinstance(v, tuple):
                    if test:
                        v = v[0]
                    else:
                        v = v[1]

                out[state][k] = v

    return out
