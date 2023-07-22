"""
Test suite for Salt execution modules in the Juniper Junos formula
Copyright (C) 2023 SUSE LLC <georg.pfuetzenreuter@suse.com>

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

from lib import api, salt
import pytest

@pytest.mark.skip(reason="doesn't work consistently, unsure about the expected behavior (FIXME)")
@pytest.mark.parametrize('arguments', ['parents_only=False', ''])
def test_susejunos_get_active_interfaces(host, device, arguments):
    rout, rerr, rc = salt(host, device, f'susejunos.get_active_interfaces {arguments}')
    print(rout)
    assert not rerr
    if arguments == '':
        assert not len(rout)
    else:
        assert len(rout)
        assert 'fxp0' in rout

def test_susejunos_get_active_vlans(host, device, vlan):
    rout, rerr, rc = salt(host, device, f'susejunos.get_active_vlans')
    print(rout)
    assert not rerr
    assert 'parsed_vlan_dict' in rout
    # does the VLAN ID really need to be string ?
    assert '99' in rout['parsed_vlan_dict']
    assert rout['parsed_vlan_dict']['99'] == 'pytest-vlan'
    assert not rout['unparsed_vlan_list']
