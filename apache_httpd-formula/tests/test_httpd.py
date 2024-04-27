"""
Test suite for assessing the apache_httpd formula
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

import pytest

@pytest.mark.parametrize(
  'pillar, package', [
    ({}, 'apache2-event'),
    ({'sysconfig': {'APACHE_MPM': 'prefork'}}, 'apache2-prefork')
  ],
  indirect=['pillar']
)
@pytest.mark.parametrize('test', [True, False])
def test_httpd_package(host, package, pillar, salt_apply, test):
  result = salt_apply
  assert len(result) > 0
  output = result[0]
  state = 'pkg_|-apache_httpd_packages_|-apache_httpd_packages_|-installed'
  assert state in output
  assert output[state].get('name') == 'apache_httpd_packages'
  changes = output[state].get('changes')
  if test:
    assert changes == {package: {'new': 'installed', 'old': ''}}
  else:
    assert package in changes
    assert 'apache2-utils' in changes
    # in non-test runs, "new" will return the freshly installed version, such as 2.4.51-150400.6.14.1
    assert '2.4' in changes[package]['new']
  print(output)
  assert host.package('apache2').is_installed is not test
  assert host.package(package).is_installed is not test


@pytest.mark.parametrize('test', [True, False])
def test_httpd_config(host, salt_apply, test):
  result = salt_apply
  assert len(result) > 0
  output = result[0]
  for file, checksum in {
    'conf.d/remote.conf': '2d4e69a65a3c77743f8504af4ae2415a',
    'vhosts.d/mysite1.conf': '15edeaf0ea295a192e9aa964b011493f',
    'vhosts.d/mysite2.conf': 'b11ed81a8d1e8f2c5f48a89e9df8c757',
    'vhosts.d/status.conf': '41228b88bdb6156773b4e26c39c5d9bc',
  }.items():
    if file.startswith('conf.d'):
      place = 'configs'
    elif file.startswith('vhosts.d'):
      place = 'vhosts'
    file = f'/etc/apache2/{file}'
    state = f'file_|-apache_httpd_{place}_|-{file}_|-managed'
    assert state in output
    assert output[state].get('name') == file
    changes = output[state].get('changes')
    if test:
      assert changes == {'newfile': file}
      assert output[state]['result'] is None
    else:
      assert changes == {'diff': 'New file', 'mode': '0644'}
      file = host.file(file)
      assert file.is_file
      assert file.uid == 0
      assert file.gid == 0
      assert file.md5sum == checksum


@pytest.mark.parametrize('test', [True, False])
def test_httpd_sysconfig(host, salt_apply, test):
  result = salt_apply
  assert len(result) > 0
  output = result[0]
  state = 'suse_sysconfig_|-apache_httpd_sysconfig_|-apache2_|-sysconfig'
  assert state in output
  file = '/etc/sysconfig/apache2'
  changes = output[state].get('changes')
  assert output[state].get('name') == file
  assert output[state]['result'] is True
  if test:
    assert changes == {}
    assert 'unable to open' in output[state]['comment']
  else:
    assert 'diff_config' in changes 
    assert 'diff_header' in changes
    file = host.file(file)
    assert file.contains('^APACHE_MPM="event"$')
    assert file.contains('^APACHE_SERVERADMIN=""$')
    assert file.contains('^APACHE_SERVERNAME="ipv6-localhost"$')


@pytest.mark.parametrize('test', [False])
def test_httpd_service(host, salt_apply, test):
    assert host.service('apache2').is_enabled
    assert host.service('apache2').is_running
