"""
Test suite for assessing the Redis formula configuration results
Copyright (C) 2023-2024 SUSE LLC <georg.pfuetzenreuter@suse.com>

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

import pytest

@pytest.fixture
def instance():
    return {
            'config': '/etc/redis/foo.conf',
            'socket': '/run/redis/foo.sock',
            'datadir': '/var/lib/redis/foo',
            'logfile': '/var/log/redis/foo.log',
            'pidfile': '/run/redis/foo.pid',
            'service': 'redis@foo'
        }

def test_redis_config_file_exists(host, instance):
    with host.sudo():
        exists = host.file(instance['config']).exists
    assert exists is True

def test_redis_config_file_contents(host, instance):
    with host.sudo():
        struct = host.file(instance['config']).content_string
    for line in [
            'timeout 0',
            'supervised systemd',
            f'unixsocket {instance["socket"]}',
            'unixsocketperm 460',
            f'pidfile {instance["pidfile"]}',
            f'logfile {instance["logfile"]}',
            f'dir {instance["datadir"]}',
        ]:
        assert line in struct

def test_redis_config_file_permissions(host, instance):
    with host.sudo():
        file = host.file(instance['config'])
    assert file.user == 'root'
    assert file.group == 'redis'
    assert oct(file.mode) == '0o640'

def test_redis_service(host, instance):
    assert host.service(instance['service']).is_enabled
