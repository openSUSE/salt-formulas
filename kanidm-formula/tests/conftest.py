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

@pytest.fixture
def idm_admin(host):
    return idm_admin_password(host)

@pytest.fixture(scope='module')
def clean_accounts(host):
    yield

    print(host.run(f'env KANIDM_PASSWORD={idm_admin_password(host)} kanidm -D idm_admin login && for x in testperson1 testperson2; do echo $x; kanidm -D idm_admin person delete "$x"; done'))
