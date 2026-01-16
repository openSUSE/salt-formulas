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

from shlex import quote

import pytest
from utils import (DSCONF_FILE, INSTANCE, SUFFIX, cmd, cmd_dsconf,
                   instance_setup, instance_teardown, salt)


@pytest.fixture(scope='module')
def instance(host):
    instance_setup(host)

    yield INSTANCE

    instance_teardown(host)


# this would be better with module scope, but causes wrong ordering for some reason?
@pytest.fixture()
def instance_with_samples(host):
    instance_setup(host, True)

    yield INSTANCE

    instance_teardown(host)


@pytest.fixture()
def replications(host):
    t_repls = [
            {'role': 'supplier', 'replica-id': 1, 'bind-dn': 'cn=replication manager,cn=config', 'bind-passwd': 'muchsecretmuchwow'},
            # TODO: multiple suffixes + replications
            #{'role': 'consumer', 'replica-id': 65535, 'bind-dn': 'cn=replication manager,cn=config', 'bind-passwd': 'muchsecretmuchwow'},
        ]

    for r in t_repls:
        result = host.run(cmd_dsconf([
            INSTANCE, 'replication', 'enable',
            '--suffix', SUFFIX, '--role', r['role'], '--replica-id', str(r['replica-id']), '--bind-dn', r['bind-dn'], '--bind-passwd', r['bind-passwd']
        ]))
        print(result)
        if result.rc != 0:
            print(r)
            pytest.fail('Could not create testing replication.')

    yield t_repls

    for r in t_repls:
        result = host.run(f'sudo dsconf {INSTANCE} replication list | grep ^{SUFFIX}$')
        if result.rc != 0:
            print('Replication not present.')
            continue
        result = host.run(cmd_dsconf([INSTANCE, 'replication', 'disable', '--suffix', SUFFIX]))
        print(result)
        if result.rc != 0:
            pytest.fail('Could not delete testing replication.')


@pytest.fixture
def pillar(request):
    # this can be used to expand the pillar
    return request.param


@pytest.fixture
def salt_state_apply(host, pillar, test):
    print(f'sa pillar: {pillar}')
    print(f'sa test: {test}')

    pillar = quote(str(pillar))

    yield salt(host, f'state.apply 389ds pillar={pillar} test={test}')

    # loose cleanup regardless of whether the above changed anything
    host.run(cmd(['sudo', 'dsctl', INSTANCE, 'remove', '--do-it']))
    host.run('rpm --quiet -q 389-ds && sudo zypper -nq rm 389-ds')
    host.run(cmd(['sudo', 'rm', '-f', DSCONF_FILE]))
