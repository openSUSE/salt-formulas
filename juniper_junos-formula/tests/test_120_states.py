"""
Test suite for Salt states in the Juniper Junos formula
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

from lib import api, salt_apply
import pytest
import re

@pytest.mark.parametrize('state', ['firewall', 'switch'])
@pytest.mark.parametrize('test', [True, False])
def test_apply(host, device, state, test):
    """
    Test to assess whether the device gets the expected configuration applied without any errors
    """
    if state == 'firewall' and 'qfx' in device:
        pytest.skip('Skipping firewall test on switch')
    if state == 'switch' and 'srx' in device:
        pytest.skip('Skipping switch test on firewall')
    rout, rerr, rc = salt_apply(host, device, f'juniper_junos.{state}', test)
    assert not rerr
    stateout = rout[f'netconfig_|-junos_{state}_|-junos_{state}_|-managed']
    assert stateout['name'] == f'junos_{state}'
    assert bool(stateout['changes']) is not test
    assert stateout['comment']
    if test:
        assert 'Configuration discarded.' in stateout['comment']
        assert 'Configuration diff:' in stateout['comment']
        assert 'Loaded config:' in stateout['comment']
    else:
        assert 'Configuration changed!\n' == stateout['comment']
        assert stateout['changes']['loaded_config']
    diffs_firewall = [
            '+           any notice;',
            '+           authorization info;',
            '+           interactive-commands any;',
            '+  vlans {',
            '+  chassis {',
            '+      cluster {',
            '+          reth-count 1;',
            '+          redundancy-group 1 {',
            '+              node 1 priority 10;',
            '+   ge-0/0/1 {',
            '+       mtu 9100;',
            '+       ether-options {',
            '+           redundant-parent reth0;',
            '+   reth0 {',
            '+       description test;',
            '+       mtu 9100;',
            '+       redundant-ether-options {',
            '+           redundancy-group 1;',
            '+       unit 0 {',
            '+           family ethernet-switching {',
            '+               interface-mode access;',
            '+               vlan {',
            '+                   members 1;'
        ]
    diffs_switch = [
            '-    user \* {',
            '-        any emergency;',
            '\[edit system syslog file messages\]\n\+     interactive-commands any;',
            '-    file interactive-commands {',
            '-        interactive-commands any;',
            '-   default {',
            '-       vlan-id 1;',
            '\[edit protocols\]\n\+   iccp {',
            '+       local-ip-addr 192.168.1.1;',
            '+       local-ip-addr 192.168.1.1;',
            '+       peer 192.168.1.2 {',
            '+           session-establishment-hold-time 340;',
            '+           redundancy-group-id-list 1;',
            '+           backup-liveness-detection {',
            '+               backup-peer-ip 192.168.1.3;',
            '+           }',
            '+           liveness-detection {',
            '+               version automatic;',
            '+               minimum-interval 5000;',
            '+               transmit-interval {',
            '+                   minimum-interval 1000;',
            '+               }',
            '+           }',
            '+       }',
            '+   }',
        ]
    diffs_shared = [
            '+   ge-0/0/2 {',
            '+       description foo;',
            '+       mtu 9100;',
            '+       unit 0 {',
            '+           description bar;',
            '+           family inet {',
            '+               address 192.168.99.1/32;',
            '+           family inet6 {',
            '+               address fd15:5695:f4b6:43d5::1/128;',
            '+   ge-0/0/3 {',
            '+       ether-options {',
            '+           802.3ad ae0;',
            '+   ge-0/0/4 {',
            '+       mtu 9000;',
            '+       unit 0 {',
            '+           family ethernet-switching {',
            '+               interface-mode trunk;',
            '+               vlan {',
            '+                   members 1-2;',
            '+   ae0 {',
            '+       description Katze;',
            '+       mtu 9100;',
            '+       aggregated-ether-options {',
            '+           lacp {',
            '+               system-id ff:ff:ff:ff:ff:ff;',
            '+               admin-key 65535;',
            '+               force-up;',
            '+   irb {',
            '+       mtu 1500;',
            '+       unit 900 {',
            '+           family inet {',
            '+               address 192.168.98.1/30;',
            '+           }',
            '+       }',
            '+   }',
            '+  \s+vlan1 {',
            '+      \s+vlan-id 1;',
            '+  \s+vlan2 {',
            '+      \s+vlan-id 2;',
            '+      \s+l3-interface irb.900;',
            '+  \s+vlan200 {',
            '+      \s+description baz;',
            '+      \s+vlan-id 200;'
        ]
    if 'srx' in device:
        diffs = diffs_shared + diffs_firewall
    else:
        diffs = diffs_shared + diffs_switch
    if test:
        target = stateout['comment']
    else:
        target = stateout['changes']['diff']
    for text in diffs:
        if text.startswith('+'):
            text = text.replace('+', '\+', 1)
        assert bool(re.search(text, target))
