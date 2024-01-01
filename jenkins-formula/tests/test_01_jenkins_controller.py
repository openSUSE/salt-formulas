"""
Test suite for assessing the Jenkins Controller configuration results
Copyright (C) 2023-2024 Georg Pfuetzenreuter <georg.pfuetzenreuter@suse.com>

This program is free software: you can jenkinstribute it and/or modify
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

import yaml

confdir = '/etc/jenkins'
conffile = f'{confdir}/salt.yaml'

def test_jenkins_package(host):
    assert host.package('jenkins').is_installed

def test_jenkins_config_file_exists(host):
    with host.sudo():
        assert host.file(conffile).exists

def test_jenkins_config_file_contents(host):
    pillar = {'jenkins': {
                'systemMessage': 'Deployed with Salt!'
                },
              'unclassified': {
                'location': {
                  'url': 'https://example.com'
                  }
                }
              }
    with host.sudo():
        struct = yaml.safe_load(host.file(conffile).content_string)
        assert pillar.items() == struct.items()

def test_jenkins_config_file_permissions(host):
    with host.sudo():
        file = host.file(conffile)
        assert file.user == 'root'
        assert file.group == 'jenkins'
        assert oct(file.mode) == '0o640'

def test_jenkins_service(host):
    assert host.service('jenkins').is_enabled
