"""
Helpers for testing the apache_httpd formula
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
    #print(result)
    output = loads(result.stdout)['local']
    return output, result.stderr, result.rc

@pytest.fixture
def pillar(request):
    with open('apache_httpd-formula/tests/pillar.sls') as fh:
      pillar = safe_load(fh)
    if hasattr(request, 'param'):
      print(request.param)
      pillar['apache_httpd'].update(request.param)
    return pillar

@pytest.fixture
def salt_apply(host, pillar, test):
    print(f'sa pillar: {pillar}')
    print(f'sa test: {test}')
    yield salt(host, f'state.apply apache_httpd pillar="{pillar}" test={test}')
    host.run('zypper -n rm -u apache2')
    host.run('rm -fr /etc/apache2 /etc/sysconfig/apache2 /var/cache/apache2 /var/lib/apache2 /var/log/apache2')
