# -*- coding: utf-8 -*-
"""
Salt execution module with Juniper Junos related utilities
Copyright (C) 2023 SUSE LLC

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

'''
SUSE JUNOS
==========

:codeauthor: Adam Pavlidis <adampavlidis@gmail.com>
:maintainer: Georg Pfuetzenreuter <georg.pfuetzenreuter@suse.com>
:maturity:   new
:depends:    napalm
:platform:   unix

Dependencies
------------
- :mod:`NAPALM proxy minion <salt.proxy.napalm>`
'''

import os
import re
import time
import ipaddress

import logging
log = logging.getLogger(__file__)

# import NAPALM utils
import salt.utils.napalm
from salt.utils.napalm import proxy_napalm_wrap

# ----------------------------------------------------------------------------------------------------------------------
# module properties
ifname_regex = re.compile('set interfaces (\S+)\s+')
unit_regex = re.compile('set interfaces \S+\s+unit\s+(\S+)')
vlanid_regex = re.compile('set vlans (\S+)\s+vlan-id\s+(\d+)')
vlan_regex = re.compile('set vlans (\S+)')


# ----------------------------------------------------------------------------------------------------------------------

__virtualname__ = 'susejunos'
__proxyenabled__ = ['napalm']
# uses NAPALM-based proxy to interact with network devices
__virtual_aliases__ = ('susejunos',)

# ----------------------------------------------------------------------------------------------------------------------
# property functions
# ----------------------------------------------------------------------------------------------------------------------


def __virtual__():
    '''
    NAPALM library must be installed for this module to work and run in a (proxy) minion.
    '''
    return salt.utils.napalm.virtual(__opts__, __virtualname__, __file__)

# ----------------------------------------------------------------------------------------------------------------------
# helper functions -- will not be exported
# ----------------------------------------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------------------------------------
# callable functions
# ----------------------------------------------------------------------------------------------------------------------


@proxy_napalm_wrap
def get_active_interfaces(
        include_ae=True,
        include_xe=True,
        include_et=True,
        include_ge=True,
        include_reth=True,
        include_fxp=True,
        parents_only=True
):  # pylint: disable=unused-argument

    """

    :param include_ae:
    :param include_xe:
    :param include_et:
    :param include_ge:
    :param include_reth:
    :param parents_only:
    :return: list of currently installed interfaces
    """

    command = 'show configuration interfaces | display set'

    ret = __salt__['net.cli'](command,
                              inherit_napalm_device=napalm_device)  # pylint: disable=undefined-variable

    output = ret['out'][command]

    filtered_output = []
    unit_filtered_output = []

    for ln in output.split('\n'):
        match_ifname = ifname_regex.match(ln)
        match_unit = unit_regex.match(ln)
        if match_unit:
            try:
                unit = int(match_unit[1])

            except ValueError:
                unit = 0

        else:
            unit = 0

        if match_ifname:
            ifname = match_ifname[1]

            if unit:
                unitifname = f'{ifname}.{unit}'

            else:
                unitifname = ifname

            if include_ae and ifname.startswith('ae'):
                filtered_output.append(ifname)
                unit_filtered_output.append(unitifname)

            if include_xe and ifname.startswith('xe'):
                filtered_output.append(ifname)
                unit_filtered_output.append(unitifname)

            if include_et and ifname.startswith('et'):
                filtered_output.append(ifname)
                unit_filtered_output.append(unitifname)

            if include_reth and ifname.startswith('reth'):
                filtered_output.append(ifname)
                unit_filtered_output.append(unitifname)

            if include_ge and ifname.startswith('ge'):
                filtered_output.append(ifname)
                unit_filtered_output.append(unitifname)

            if include_fxp and ifname.startswith('fxp'):
                filtered_output.append(ifname)
                unit_filtered_output.append(unitifname)

    if not parents_only:
        filtered_output = unit_filtered_output

    return sorted(list(set(filtered_output)))


@proxy_napalm_wrap
def get_active_vlans():  # pylint: disable=unused-argument
    """
    parses the configuration of juniper to retrieve vlans parsed and unparsed

    :return: {'parsed_vlan_dict': {}, 'unparsed_vlan_list': []}
    """

    command = 'show configuration vlans | display set'

    ret = __salt__['net.cli'](command,
                              inherit_napalm_device=napalm_device)  # pylint: disable=undefined-variable

    log.debug(f'Return output {ret}')

    output = ret['out'][command]

    vlan_noid = set()
    parsed_vlans = {}

    for ln in output.split('\n'):
        match_vlan = vlan_regex.match(ln)
        match_vlanid = vlanid_regex.match(ln)

        if match_vlanid:
            vlan_name = match_vlanid[1]
            vlan_id = match_vlanid[2]

            if vlan_id not in parsed_vlans:
                parsed_vlans[int(vlan_id)] = vlan_name
                if vlan_name in vlan_noid:
                    vlan_noid.remove(vlan_name)

            else:
                log.error('Something very wrong is happening here %s exists in %s', vlan_id, parsed_vlans)

        else:
            if match_vlan and match_vlan[1] not in parsed_vlans.values():
                vlan_noid.add(match_vlan[1])

    return {'parsed_vlan_dict': parsed_vlans, 'unparsed_vlan_list': list(vlan_noid)}
