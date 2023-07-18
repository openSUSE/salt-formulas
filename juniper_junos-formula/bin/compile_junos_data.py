#!/usr/bin/python3
"""
Juniper Junos Salt pillar generator
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

import argparse
import logging
import pathlib
import sys
import yaml

logger = logging.getLogger(__name__)
log_choices_converter = {
        'debug': logging.DEBUG,
        'info': logging.INFO
        }
argparser = argparse.ArgumentParser()
argparser.add_argument('--log', type=str, default='info', choices=log_choices_converter.keys())
argparser.add_argument('--in-switching', type=str, default='switching.yaml')
argparser.add_argument('--in-backbone', type=str, default='backbone.yaml')
argparser.add_argument('--out', type=str, default='output')
args = argparser.parse_args()

infile_s = args.in_switching
infile_b = args.in_backbone
outdir = args.out

def _fail(msg):
    logger.error(f'{msg}, bailing out.')
    sys.exit(1)

def generate_switch_pillars(data):
    all_pillars = {}
    global_port_groups = data.get('port_groups', {})
    ignore_ports = data.get('ignore_ports', {})
    global_ignore_ports = ignore_ports.get('global', [])

    core = []
    aggregation = []
    access = []

    for device in data.get('switches', []):
        device_type = device.get('type')
        device_role = device.get('role')
        device_id = device.get('id')
        if device_type == 'switch':
            if device_role == 'core':
                core.append(device_id)
            elif device_role == 'aggregation':
                aggregation.append(device_id)
            elif device_role == 'access':
                access.append(device_id)
            else:
                _fail(f'Illegal switch role "{device_role}" in device {device}')

    logger.debug(f'Core switches: {core}')
    logger.debug(f'Aggregation switches: {aggregation}')
    logger.debug(f'Access switches: {access}')

    switch_pillar = {
            device: {
                'vlans': {},
                'vlan_set': set(),
                'lacp': {},
                'ports': {},
                'ignore_ports': global_ignore_ports
            } for device in core + aggregation + access
        }

    for device, config in switch_pillar.items():
        if device in ignore_ports:
            if ignore_ports[device] not in switch_pillar[device]['ignore_ports']:
                switch_pillar[device]['ignore_ports'] += ignore_ports[device]

    ## Compatibility helper for the old, list based, input format
    data_vlans = data.get('vlans')
    if isinstance(data_vlans, list):
        vlans = {}
        for vlan in data_vlans:
            vlan_id = vlan.get('id')
            vlan_name = vlan.get('name')
            vlan_description = vlan.get('description')
            vlan_groups = vlan.get('groups')
            vlans.update({
                vlan_name: {
                    'id': vlan_id,
                    'description': vlan_description
                }
            })
            if vlan_groups:
                vlans[vlan_name].update({'groups': vlan_groups})
        logger.debug(f'Converted legacy VLANs: {vlans}')
    elif isinstance(data_vlans, dict):
        vlans = data_vlans

    for vlan, vconfig in vlans.items():
        vlan_id = vconfig.get('id')
        vlan_description = vconfig.get('description')

        logger.debug(f'Processing VLAN {vlan} with ID {vlan_id}')

        for group in vconfig.get('groups', []):
            logger.debug(f'Processing group {group}')

            if group in global_port_groups:
                for group, gconfig in global_port_groups[group].items():
                    group_description = gconfig.get('description')
                    group_members = gconfig.get('members', [])

                    if vlan_id in switch_pillar[group]['vlan_set']:
                        logger.debug(f'VLAN {vlan} already exists in set.')
                    else:
                        # ??
                        switch_pillar[group]['vlan_set'] = switch_pillar[group]['vlan_set'].union({vlan_id})
                        switch_pillar[group]['vlans'].update({vlan: {'id': vlan_id, 'description': vlan_description}})

                    for port in group_members:
                        if not 'iface' in port:
                            logger.debug(f'Skipping {port}')
                            continue

                        interface = port['iface']

                        if interface in switch_pillar[group]['ignore_ports']:
                            _fail(f'Attempted to configure interface {interface}, but it is set to be ignored. This should not happen')

                        interface_description = port.get('description')

                        if interface in switch_pillar[group]['ports']:
                            logger.debug(f'Interface {interface} is already in pillar')
                            tagged = switch_pillar[group]['ports'][interface]['tagged']
                            if vlan_id not in tagged:
                                tagged.append(vlan_id)

                        else:
                            switch_pillar[group]['ports'][interface] = {
                                    'interface': interface,
                                    'untagged': None,
                                    'tagged': [vlan_id],
                                    'description': interface_description
                                }

    lacp_backbone = data.get('lacp_backbone', {})
    lacp_data = {}

    for device, lacps in lacp_backbone.items():
        for lacp, lconfig in lacps.items():
            if lacp in switch_pillar[device]['ignore_ports']:
                _fail(f'Attempted to configure LACP interface {lacp}, but it is set to be ignored. This should not happen')

            for lacp_member in lconfig.get('members', []):
                lacp_interface = lacp_member.get('interface')
                logger.debug(f'Computing LACP member interface {lacp_interface}')

                if interface in switch_pillar[device]['ignore_ports']:
                    _fail(f'Attempted to configure LACP member interface {interface}, but it is set to be ignored. This should not happen')

                if not lacp_interface in lacp_data[device]:
                    lacp_data[device] = {lacp_interface: {}}

                lacp_data[device][lacp_interface] = {
                        'parent': lacp_id,
                        'description': lconfig.get('description', f'member_of_lag_{lacp_id}')
                    }

    logger.debug(f'LACP backbone data: {lacp_data}')

    lacp_switch = data.get('lacp', {})
    lacp_interfaces = {}

    for device, interfaces in lacp_switch.items():
        ## Compatibility helper for old, list based, input data
        if isinstance(interfaces, list):
            interfaces = {}
            for interface in interfaces:
                if_lacp_id = interface.get('lacp_id')
                if if_lacp_id:
                    lacp_interfaces[if_lacp_id] = {}
                    ifd = lacp_interfaces[if_lacp_id]
                    if_members = interface.get('members')
                    if isinstance(if_members, list):
                        ifd_members = {}
                        for member in if_members:
                            ifd_members.update({
                                member.get('iface'): {
                                    'description': member.get('description')
                                }
                            })
                    elif isinstance(if_members, dict):
                        ifd_members = if_members
                    if_lacp_options = interface.get('lacp_options')
                    if_mclag_options = interface.get('mclag_options')
                    if if_members:
                        ifd.update({'members': ifd_members})
                    if if_lacp_options:
                        ifd.update({'lacp_options': if_lacp_options})
                    if if_mclag_options:
                        ifd.update({'mclag_options': if_mclag_options})
            logger.debug(f'Converted legacy LACP interfaces: {lacp_interfaces}')
        elif isinstance(lacp_interfaces, dict):
            lacp_interfaces = interfaces
        else:
            _fail(f'Invalid LACP data structure')

        for ae_interface, ifconfig in lacp_interfaces.items():
            lacp_id = ifconfig.get('lacp_id')
            if lacp_id in [elem.get('lacp_id') for elem in lacp_backbone.get(device, [])]:
                logger.warning(f'Re-declared interface {device} {ae_interface}')
                continue

            if lacp_id in switch_pillar[device]['ignore_ports']:
                logger.warning(f'Ignoring ignored interface {device} {ae_interface}')
                continue

            for member_interface, mconfig in ifconfig.get('members', {}).items():
                if member_interface in lacp_data.get(device, {}):
                    logger.warning(f'Ignoring backbone interface {device} {member_interface}')
                    continue
                else:
                    if member_interface in switch_pillar[device]['ignore_ports']:
                        logger.warning(f'Igoring ignored interface {member_interface}')
                        continue

                    if not device in lacp_data:
                        lacp_data[device] = {}

                    if not member_interface in lacp_data[device]:
                        lacp_data[device][member_interface] = {}

                    lacp_data[device][member_interface] = {
                            'parent': lacp_id,
                            'description': mconfig.get('description', f'member_of_lag_{lacp_id}')
                        }

    for device, dconfig in lacp_data.items():
        logger.debug('Processing LACP data {device} {dconfig}')

        remove_ports = []

        for member in dconfig.keys():
            if device in switch_pillar and member in switch_pillar[device]['ports']:
                remove_ports.append(member)

        for port in remove_ports:
            logger.warning(f'Popping backbone link {device} {member}')
            dconfig.pop(member)

        switch_pillar[device]['lacp'] = dconfig

    for device, pconfig in data.get('ports', {}).items():
        logger.debug(f'Processing port {device} {pconfig}')
        for member in pconfig.keys():
            if device in switch_pillar:
                dpillar = switch_pillar[device]
                if member in dpillar['ports']:
                    logger.warning(f'Ignoring backbone link {device} {member}')
                    continue
                elif member in dpillar['lacp']:
                    logger.warning(f'Ignoring LACP slave {device} {member}')
                    continue
                elif member in dpillar['ignore_ports']:
                    logger.warning(f'Ignoring ignored port {device} {member}')
                    continue
                else:
                    dpillar['ports'][member] = pconfig[member]

    for device in lacp_switch.keys():
        for lacp, lconfig in lacp_interfaces.items():
            interface = lconfig.get('lacp_id')
            if interface in [elem.get('lacp_id') for elem in lacp_backbone.get(device, [])]:
                logger.debug(f'Skipping LACP interface {interface}')
                continue

            lacp_options = lconfig.get('lacp', {})
            mclag_options = lconfig.get('mclag', {})

            mclag_options.setdefault('mc-ae-id', 1)
            mclag_options.setdefault('redundancy-group', 1)

            if device.endswith('1'):
                mclag_options.setdefault('chassis-id', 0)
                mclag_options.setdefault('status-control', 'active')
            elif device.endswith('2'):
                mclag_options.setdefault('chassis-id', 1)
                mclag_options.setdefault('status-control', 'passive')
            else:
                logger.debug(f'Unable to determine chassis-id and status-control for interface {device} {interface}')

            interface_pillar = switch_pillar[device]['ports'][interface]
            if not 'lacp_options' in interface_pillar and 'mclag_options' in interface_pillar:
                logger.warning(f'LACP interface {device} {interface} without switching configuration?')
                switch_pillar[device]['ports'][interface] = {
                        'description': lconfig.get('description'),
                        'lacp_options': lacp_options,
                        'mclag_options': mclag_options
                    }

    for device, lacps in lacp_backbone.items():
        for lacp, lconfig in lacps.items():
            interface = lconfig.get('lacp_id')
            lacp_options = lconfig.get('lacp', {})
            mclag_options = lconfig.get('mclag', {})


            # FIXME, this is redundant with the lacp_switch loop above
            mclag_options.setdefault('mc-ae-id', 1)
            mclag_options.setdefault('redundancy-group', 1)

            if device.endswith('1'):
                mclag_options.setdefault('chassis-id', 0)
                mclag_options.setdefault('status-control', 'active')
            elif device.endswith('2'):
                mclag_options.setdefault('chassis-id', 1)
                mclag_options.setdefault('status-control', 'passive')
            else:
                logger.debug(f'Unable to determine chassis-id and status-control for interface {device} {interface}')

            interface_pillar = switch_pillar[device]['ports'][interface]
            if not 'lacp_options' in interface_pillar and 'mclag_options' in interface_pillar:
                logger.warning(f'LACP interface {device} {interface} without switching configuration?')
                switch_pillar[device]['ports'][interface] = {
                        'description': lconfig.get('description'),
                        'lacp_options': lacp_options,
                        'mclag_options': mclag_options
                    }

    for device, config in switch_pillar.items():
        config.pop('vlan_set')
        all_pillars[device] = config

    return all_pillars


def main():
    for file in [infile_s, infile_b]:
        if not pathlib.Path(file).is_file():
            _fail(f'Unable to locate "{file}"')

    if not pathlib.Path(outdir).is_dir():
        _fail(f'Directory "{outdir}" does not exist')

    with open(infile_s) as fh:
        data_s = yaml.safe_load(fh)

    with open(infile_b) as fh:
        data_b = yaml.safe_load(fh)

    data_s.update(data_b)

    all_pillars = generate_switch_pillars(data_s)

    for device, config in all_pillars.items():
        with open(f'{outdir}/{device}.sls', 'w') as fh:
            yaml.dump(config, fh)

    logger.info('ok')

if __name__ == '__main__':
    logger = logging.getLogger()
    logger.setLevel(log_choices_converter[args.log])
    logger.addHandler(logging.StreamHandler(sys.stdout))
    logger.debug(args)
    main()
