"""
Test suite for assessing the Redmine formula configuration results
Copyright (C) 2023-2024 Georg Pfuetzenreuter <mail+opensuse@georg-pfuetzenreuter.net>

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
import yaml

files = ['configuration', 'database']
confdir = '/etc/redmine'

def test_redmine_package(host):
    assert host.package('redmine').is_installed

def test_redmine_config_files_exist(host):
    with host.sudo():
        for file in files:
            assert host.file(f'{confdir}/{file}.yml').exists

def test_redmine_config_file_contents(host):
    pillar = {'configuration': {
                'default': {
                  'email_delivery': {
                    'delivery_method': ':smtp',
                    'smtp_settings': {
                      'address': 'mailer@example.com',
                      'port': 25
                    }
                  }
                }
              },
              'database': {
                'production': {
                  'adapter': 'mysql2',
                  'database': 'redmine',
                  'host': 'db.example.com'
                }
              }
            }
    with host.sudo():
        for file in files:
            struct = yaml.safe_load(host.file(f'{confdir}/{file}.yml').content_string)
            assert pillar[file].items() == struct.items()

def test_redmine_config_file_permissions(host):
    with host.sudo():
        for file in files:
            file = host.file(f'{confdir}/{file}.yml')
            assert file.user == 'root'
            assert file.group == 'redmine'
            assert oct(file.mode) == '0o640'

def test_redmine_service(host):
    assert host.service('redmine').is_enabled
