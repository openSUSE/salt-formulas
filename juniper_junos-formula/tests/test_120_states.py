"""
Test suite for Salt states in the Juniper Junos formula
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

from lib import api, salt_apply
import pytest

@pytest.mark.parametrize('test', [True, False])
def test_apply_switches(host, device, test):
    rout, rerr, rc = salt_apply(host, device, f'juniper_junos.switch', test)
    assert not rerr
    stateout = rout['netconfig_|-junos_switches_|-junos_switches_|-managed']
    assert stateout['name'] == 'junos_switches'
    assert bool(stateout['changes']) is not test
    assert stateout['comment']
    if test:
        assert 'Configuration discarded.' in stateout['comment']
        assert 'Configuration diff:' in stateout['comment']
    else:
        assert 'Configuration changed!\n' == stateout['comment']
    for text in [
            '-     any any;',
            '+     any notice;',
            '+   ge-0/0/7 {',
            '+   ge-0/0/8 {',
            '+   ae1 {',
            '+       description "Sample trunk on port 7";',
            '+       description "Sample trunk on port 8";',
            '+       description "Sample aggregated port group";',
            '+      vlan10 {',
            '+          description "Sample VLAN";',
            '+          vlan-id 10;',
        ]:
        if test:
            assert text in stateout['comment']
        else:
            assert text in stateout['changes']['diff']

