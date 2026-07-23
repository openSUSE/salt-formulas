"""
Copyright (C) 2026 Georg Pfuetzenreuter <mail+opensuse@georg-pfuetzenreuter.net>

This program is free software: you can redminetribute it and/or modify
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

import pytest

def idm_admin_password(host):
    result = host.run(f'sudo kanidmd -o json recover-account idm_admin')
    print(result)
    for line in result.stdout.splitlines():
        if line[0] == '{':
            return loads(line)['password']
        if line[0] == '"':
            return loads(line)
    return None

def login_cmd(host, password=None):
    if password is None:
        password = idm_admin_password(host)
    return f'env KANIDM_PASSWORD={password} kanidm -D idm_admin login'

@pytest.fixture
def idm_admin(host):
    return idm_admin_password(host)

@pytest.fixture(scope='module')
def people_accounts_only_delete(host):
    yield

    print(host.run(f'{login_cmd(host)} && for x in testperson1 testperson2; do echo $x; kanidm -D idm_admin person delete "$x"; done'))

@pytest.fixture(scope='module')
def service_accounts_only_delete(host):
    yield

    # for some reason accounts must be deleted from groups first, otherwise account delete will return 403 (very helpful indeed)
    print(host.run(f'{login_cmd(host)} && for a in testsvc1 testsvc2 testsvc3 testsvc4; do echo $x; for g in idm_people_admins idm_service_account_admins; do kanidm -D idm_admin group remove-members $g $a; done; kanidm -D idm_admin service-account delete $a; done'))

@pytest.fixture
def account(host):
    name = 'testperson3'
    password = idm_admin_password(host)
    login = login_cmd(host, password)

    print(host.run(f'{login} && kanidm -D idm_admin person create {name} "Full name of {name}"'))

    yield (name, password)

    print(host.run(f'{login} && kanidm -D idm_admin person delete {name}'))
