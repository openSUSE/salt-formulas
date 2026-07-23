"""
Copyright (C) 2025-2026 Georg Pfuetzenreuter <mail+opensuse@georg-pfuetzenreuter.net>

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
from utils import salt
import pytest

@pytest.mark.parametrize(
        'name, success', [
            ('idm_admin', True),
            ('boobaz', False),
        ],
)
def test_kanidm_client_local_login(host, name, success, idm_admin):
    if name == 'idm_admin':
        password = idm_admin
    else:
        password = 'garbage'
    out, err, rc = salt(host, f'kanidm_client.local_login {name} {password}')
    if success:
        assert rc == 0
    else:
        assert rc == 1
    assert out == success

@pytest.mark.parametrize(
        'name, displayname, managed_by, groups, success', [
            ('testsvc1', 'Test Service 1', 'idm_admin', ['idm_service_account_admins@idm.example.com'], True),
            ('testsvc1', 'Test Service 2', 'idm_admin', ['idm_service_account_admins'], False),
            ('testsvc1', 'Test Service 2', 'idm_admin', [], False),
            ('testsvc2', 'Test Service 2', 'idm_admin', ['idm_service_account_admins', 'idm_people_admins'], True),
            ('testsvc3', 'Test Service 3', 'boo_not_exist', ['idm_service_account_admins', 'idm_people_admins'], False),
            ('testsvc3', 'Test Service 3', 'boo_not_exist', [], False),
        ],
)
def test_kanidm_client_local_service_account_create(host, idm_admin, service_accounts_only_delete, name, displayname, managed_by, groups, success):
    out, err, rc = salt(host, f'kanidm_client.local_login idm_admin {idm_admin}')
    if rc != 0:
        pytest.fail('could not authenticate for testing local_service_account_create() test')

    cmd = f'kanidm_client.local_service_account_create {name} "{displayname}" {managed_by}'
    if groups:
        cmd = f'{cmd} "{groups}"'
    out, err, rc = salt(host, cmd)
    if success:
        assert rc == 0
    else:
        assert rc == 1
    assert out == success

@pytest.mark.parametrize(
        'name, displayname, success', [
            ('testperson1', 'Test Person 1', True),
            ('testperson1', 'Test Person 2', False),
        ],
)
def test_kanidm_client_person_create(host, idm_admin, people_accounts_only_delete, name, displayname, success):
    out, err, rc = salt(host, f'kanidm_client.person_account_create {name} "{displayname}"')
    if success:
        assert rc == 0
        assert out == True
    else:
        assert rc == 0 ## TODO
        assert out == False

def test_kanidm_client_person_update(host, account):
    # TODO: test update of all supported fields
    new_displayname = 'The new displayname'
    name, admin_password = account

    out, err, rc = salt(host, f'kanidm_client.person_account_update {name} displayname="{new_displayname}"')
    assert rc == 0
    assert out == True

    check = host.run(f'env KANIDM_PASSWORD={admin_password} kanidm -D idm_admin login >/dev/null && kanidm -D idm_admin -o json person get {name}')
    if check.rc != 0:
        pytest.fail('could not retrieve validation result')
    have_displayname = loads(check.stdout).get('attrs', {}).get('displayname')

    # kanidm will return a list for each attribute, but only one value is expected for displayname
    if not isinstance(have_displayname, list) or len(have_displayname) != 1:
        pytest.fail('unexpected validation result')
    have_displayname = have_displayname[0]

    assert have_displayname == new_displayname
