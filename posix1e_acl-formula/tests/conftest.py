"""
Helpers for testing the posix1e_acl formula
Copyright (C) 2024 Georg Pfuetzenreuter <mail+opensuse@georg-pfuetzenreuter.net>

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
from yaml import safe_load
import pytest

def salt(host, command):
    result = host.run(f'salt-call --local --out json {command}')
    output = loads(result.stdout)['local']
    return output, result.stderr, result.rc

@pytest.fixture
def pillar(request):
    pillar = {'acl': {}}
    if hasattr(request, 'param'):
      print(request.param)
      pillar['acl'].update(request.param)
    return pillar

@pytest.fixture
def salt_apply(host, pillar, test):
    print(f'sa pillar: {pillar}')
    print(f'sa test: {test}')
    host.run('touch /tmp/posix1e_formula_acl_test{1,2,3}')  # temporary file through pytest on remote host possible? needs to align with pillar.
    yield salt(host, f'state.apply posix1e_acl pillar="{pillar}" test={test}')
    #host.run('zypper -n rm -u python*-pyacl')  # needs to be installed to evaluate test mode ...
    host.run('rm -f /tmp/posix1e_formula_acl_test*')
