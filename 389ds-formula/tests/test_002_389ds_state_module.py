"""
Test suite for Salt state modules in the 389-DS formula
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


@pytest.mark.parametrize('test', [True, False])
def test_manage_data(host, instance, test):
    """
    Test for 389ds.manage_data.
    As 389ds.manage_data is just a wrapper over ldap.managed, we only test the altered error handling here.
    """
    out, err, rc = salt(host, (
        'state.single'
        ' 389ds.manage_data'
        ' name=teststate'
        ' entries={}'
        ' connect_spec={}'
        f' test={test}'
    ))

    _id = '389ds_|-teststate_|-teststate_|-manage_data'

    if _id not in out:
        pytest.fail('Unexpected state output')

    lowout = out[_id]

    assert lowout['name'] == 'teststate'

    if test:
        assert rc == 0
        assert lowout['result'] is None
        assert 'Ignoring LDAP error' in lowout['comment']
    else:
        assert rc == 1
        assert lowout['result'] is False

    assert 'exception in ldap backend' in lowout['comment']


@pytest.mark.parametrize('test', [True, False])
def test_manage_replication(host, instance, test):
    """
    Test for 389ds.manage_replication.
    """
    out, err, rc = salt(host, (
        'state.single'
        ' 389ds.manage_replication'
        ' name=teststate'
        f' instance={INSTANCE}'
        f' suffix={SUFFIX}'
        ' role=supplier'
        ' replica_id=1'
        ' bind_dn=cn=replmanager,cn=config'
        ' bind_passwd=rllysecret'
        f' test={test}'
    ))

    assert rc == 0

    _id = '389ds_|-teststate_|-teststate_|-manage_replication'

    if _id not in out:
        pytest.fail('Unexpected state output')

    lowout = out[_id]

    assert lowout['name'] == 'teststate'

    if test:
        assert lowout['result'] is None
        assert lowout['comment'] == f'Would create replication for {SUFFIX}.'

    else:
        assert lowout['result'] is True
        assert lowout['comment'] == f'Replication successfully enabled for "{SUFFIX}"'  # output from dsconf

    assert lowout['changes'] == {'new': {'nsds5replicaid': 1}}
