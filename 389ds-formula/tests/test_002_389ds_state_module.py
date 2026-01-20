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
from utils import INSTANCE, SUFFIX, cmd, salt


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


@pytest.mark.parametrize('test', [True, False])
def test_manage_replication_agreement_create(host, instance, replications, test):
    """
    Test for 389ds.manage_replication_agreement, where the agreement defined in the pillar does not yet exist.
    """
    agmt_name = 'testagmt'

    out, err, rc = salt(host, cmd([
        'state.single',
        '389ds.manage_replication_agreement',
        'name=teststate',
        f'instance={INSTANCE}',
        f'suffix={SUFFIX}',
        f'agmt_name={agmt_name}',
        'host=127.0.0.2',
        'port=389',
        'conn_protocol=ldap',
        'bind_dn=cn=replication manager,cn=config',
        'bind_passwd=muchsecretmuchwow',
        'bind_method=simple',
        f'test={test}',
    ]))

    assert rc == 0

    _id = '389ds_|-teststate_|-teststate_|-manage_replication_agreement'

    if _id not in out:
        pytest.fail('Unexpected state output')

    lowout = out[_id]

    assert lowout['name'] == 'teststate'

    if test:
        assert lowout['result'] is None
        assert lowout['comment'] == 'Would create replication agreement.'

    else:
        assert lowout['result'] is True
        assert lowout['comment'] == f'Successfully created replication agreement "{agmt_name}"'  # output from dsconf

    assert lowout['changes'] == {
            'new': {
                'nsds5replicahost': '127.0.0.2',
                'nsds5replicaport': '389',
                'nsds5replicatransportinfo': 'ldap',
                'nsds5replicabindmethod': 'simple',
                'nsds5replicabinddn': 'cn=replication manager,cn=config',
            },
    }


@pytest.mark.parametrize('test', [True, False])
def test_manage_replication_agreement_update(host, instance, replications, repl_agmt, test):
    """
    Test for 389ds.manage_replication_agreement, , where the agreement defined in the pillar already exists, but with values not matching the ones currently configured on the system.
    """
    agmt_name = repl_agmt

    out, err, rc = salt(host, cmd([
        'state.single',
        '389ds.manage_replication_agreement',
        'name=teststate',
        f'instance={INSTANCE}',
        f'suffix={SUFFIX}',
        f'agmt_name={agmt_name}',
        'host=localhost',
        'port=3389',
        'conn_protocol=ldap',
        'bind_dn=cn=replication manager,cn=config',
        'bind_passwd=muchsecretmuchwow',
        'bind_method=simple',
        f'test={test}',
    ]))

    assert rc == 0

    _id = '389ds_|-teststate_|-teststate_|-manage_replication_agreement'

    if _id not in out:
        pytest.fail('Unexpected state output')

    lowout = out[_id]

    assert lowout['name'] == 'teststate'

    if test:
        assert lowout['result'] is None
        assert lowout['comment'] == 'Would update the replication agreement.'

    else:
        assert lowout['result'] is True
        assert lowout['comment'] == 'Successfully updated agreement'  # output from dsconf

    assert lowout['changes'] == {
            'new': {
                'nsds5replicahost': 'localhost',
                'nsds5replicaport': '3389',
                'nsds5replicatransportinfo': 'ldap',
            },
            'old': {
                'nsds5replicahost': '127.0.0.2',
                'nsds5replicaport': '636',
                'nsds5replicatransportinfo': 'ldaps',
            },
    }
