"""
Test suite for Salt execution modules in the 389-DS formula
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

import pytest
from utils import INSTANCE, SUFFIX, salt


def test_replication_list_empty(host, instance):
    out, err, rc = salt(host, f'389ds.replication_list {INSTANCE}')
    assert rc == 0
    assert out == []


def test_replication_list_populated(host, instance, replications):
    out, err, rc = salt(host, f'389ds.replication_list {INSTANCE}')
    assert rc == 0
    assert out == [SUFFIX]


def test_replication_enable(host, instance):
    out, err, rc = salt(host, (
                        f'389ds.replication_enable {INSTANCE} suffix={SUFFIX}'
                        ' role=supplier'
                        ' replica_id=1'
                        ' bind_dn=cn=replman,cn=config'
                        ' bind_passwd=rllysecret'
    ))
    assert rc == 0
    # should be passed through from dsconf
    assert out == ('Replication successfully enabled for "dc=example,dc=com"', True)

    if host.run(f'sudo dsconf {INSTANCE} replication disable --suffix {SUFFIX}').rc != 0:
        pytest.fail('Could not clean up test replication.')


def test_replication_disable(host, instance, replications):
    out, err, rc = salt(host, f'389ds.replication_disable {INSTANCE} suffix={SUFFIX}')
    assert rc == 0
    # should be passed through from dsconf
    assert out == ('Replication disabled for "dc=example,dc=com"', True)


def test_replication_get_notexist(host, instance):
    out, err, rc = salt(host, f'389ds.replication_get {INSTANCE} suffix=blablabla')
    assert rc == 1
    assert out == ({}, False)


def test_replication_get_exist(host, instance, replications):
    out, err, rc = salt(host, f'389ds.replication_get {INSTANCE} suffix={SUFFIX}')
    assert rc == 0
    assert out[1]
    assert isinstance(out[0], dict)
    assert out[0].get('type') == 'entry'  # JSON from dsconf
