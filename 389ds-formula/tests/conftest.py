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
from utils import INSTANCE, SUFFIX, cmd_dsconf, instance_setup, instance_teardown, salt


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


        # after some preceding operation ns-slapd tends to crash with "free(): invalid pointer" - since "instance" is a module scoped fixture, restart the service here to not have further tests fail due to not being able to contact the LDAP server
        host.run('[ "$(systemctl is-active dirsrv@testidm)" = failed ] && sudo systemctl restart dirsrv@testidm')

        # this should not be needed, as part of fixture teardown is removing the replication
        # yet running the whole first test module, the last test would fail because of "Replication is already enabled for this suffix", hence this workaround
        result = host.run(f'sudo dsconf {INSTANCE} replication list | grep ^{SUFFIX}$')
        if result.rc == 0:
            print('Replication is already enabled.')
            continue


        result = host.run(cmd_dsconf([
            INSTANCE, 'replication', 'enable',
            '--suffix', SUFFIX, '--role', r['role'], '--replica-id', str(r['replica-id']), '--bind-dn', r['bind-dn'], '--bind-passwd', r['bind-passwd'],
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

        # after some preceding operation ns-slapd tends to crash with "malloc_consolidate(): unaligned fastbin chunk detected" - since "instance" is a module scoped fixture, restart the service here to not have further tests fail due to not being able to contact the LDAP server
        host.run('[ "$(systemctl is-active dirsrv@testidm)" = failed ] && sudo systemctl restart dirsrv@testidm')

        result = host.run(cmd_dsconf([INSTANCE, 'replication', 'disable', '--suffix', SUFFIX]))
        print(result)
        if result.rc != 0:
            pytest.fail('Could not delete testing replication.')


@pytest.fixture()
def repl_agmt(host):
    agmt_name = 'test-fixt-agmt'

    host.run(cmd_dsconf([
        INSTANCE, 'repl-agmt', 'create',
        '--suffix', SUFFIX,
        '--host', '127.0.0.2', '--port', '636', '--conn-protocol', 'ldaps',
        '--bind-dn', 'cn=replication manager,cn=config', '--bind-passwd', 'muchsecretmuchwow',
        '--bind-method', 'SIMPLE',
        agmt_name,
    ]))

    yield agmt_name

    print(host.run(cmd_dsconf([INSTANCE, 'repl-agmt', 'delete', '--suffix', SUFFIX, agmt_name])))


@pytest.fixture
def pillar(request):
    # this can be used to expand the pillar
    return request.param


@pytest.fixture
def salt_state_apply_main(host, pillar, test):
    print(f'sa pillar: {pillar}')
    print(f'sa test: {test}')

    pillar = quote(str(pillar))

    yield salt(host, f'state.apply 389ds pillar={pillar} test={test}')

    instance_teardown(host)


@pytest.fixture
def salt_state_apply_data(host, pillar, test):
    print(f'sa pillar: {pillar}')
    print(f'sa test: {test}')

    pillar = quote(str(pillar))

    yield salt(host, f'state.apply 389ds.data pillar={pillar} test={test}')

    instance_teardown(host)
