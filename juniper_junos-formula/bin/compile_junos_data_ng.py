#!/usr/bin/python3.11
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
import ipaddress
import logging
import pathlib
import sys
import yaml

log = logging.getLogger(__name__)
log_choices_converter = {
        'debug': logging.DEBUG,
        'info': logging.INFO
        }
argparser = argparse.ArgumentParser()
argparser.add_argument('--log', type=str, default='info', choices=log_choices_converter.keys())
argparser.add_argument('--in-devices', type=str, default='devices.yaml')
argparser.add_argument('--in-switching', type=str, default='switching.yaml')
argparser.add_argument('--out', type=str, default='output')
args = argparser.parse_args()

infile_s = args.in_switching
infile_d = args.in_devices
outdir = args.out

def _fail(msg):
    log.error(f'{msg}, bailing out.')
    sys.exit(1)

def gather(devices):
    core = []
    aggregation = []
    access = []

    for switch, config in devices.get('switches', {}).items():
        role = config.get('role')
        if role == 'core':
            core.append(switch)
        elif role == 'aggregation':
            aggregation.append(switch)
        elif role == 'access':
            access.append(switch)
        else:
            _fail(f'Illegal switch role "{role}" in device {switch}')

    log.debug(f'Core switches: {core}')
    log.debug(f'Aggregation switches: {aggregation}')
    log.debug(f'Access switches: {access}')

    return core, aggregation, access

def generate(data, devices):
    global_data = data.get('global', {})
    port_groups = data.get('port_groups', {})
    ignore_ports = global_data.get('ignore_ports', [])

    big_pillar = {}

    core, aggregation, access = gather(devices)

    small_pillar = {
            device: {
                'vlans': {},
                'interfaces': {},
                'ignore': {'interfaces': ignore_ports}
            } for device in core + aggregation + access
        }


    # skip global ignore ports for devices
    def create_interface(interface, small_interfaces):
        if interface in small_interfaces:
            log.debug(f'Interface {interface} is already in pillar')
        else:
            small_interfaces[interface] = {
              'units': {
                0: {
                  'vlan': {'ids': []}
                }
              }
            }

    def compile_devices():
        for device, d_config in data.get('devices', {}).items():

            if device in small_pillar:
                log.debug(f'Processing device {device}')
            else:
                log.warning(f'Ignoring configuration for unknown device {device}')
                continue

            for interface, i_config in d_config.get('interfaces', {}).items():
                if interface in small_pillar[device]['ignore']['interfaces']:
                    _fail(f'Attempted to configure interface {interface}, but it is set to be ignored. This should not happen?')

                small_interfaces = small_pillar[device]['interfaces']

                create_interface(interface, small_interfaces)

                small_if = small_interfaces[interface]
                small_u0 = small_if['units'][0]

                if 'description' in i_config:
                    small_if['description'] = i_config['description']

                if 'group' in i_config:
                    group = i_config['group']

                    if not group in port_groups:
                        port_groups[group] = {}

                    if not device in port_groups[group]:
                        port_groups[group][device] = []

                    port_groups[group][device].append(interface)

                if 'ae' in i_config:
                    if interface.startswith('ae'):
                        log.debug(f'Processing ae on interface {interface}')
                        ae_config = i_config['ae']

                        if not 'ae' in small_if:
                            small_if['ae'] = {}

                        small_ae = small_if['ae']

                        for ae in ['lacp', 'mc']:
                            if ae in ae_config:
                                log.debug(f'Processing {ae} on interface {interface}')
                                if not ae in small_ae:
                                    small_ae[ae] = {}

                                small_ae = small_ae[ae]

                                for l_key, l_value in ae_config[ae].items():
                                    small_ae.update({l_key: l_value})
                    else:
                        log.warning(f'Ignoring ae configuration on non-ae interface {interface}')

                if 'lacp' in i_config:
                    log.debug(f'Processing LAG on interface {interface}')
                    # maybe change lacp to lag in the formula pillar, it makes more sense as a word for 802.3ad ?
                    small_if['lacp'] = i_config['lacp']

                if 'vlan' in i_config:
                    log.debug(f'Processing VLAN on interface {interface}')
                    vlan_config = i_config['vlan']

                    small_vlan = small_u0['vlan']

                    if 'ids' in vlan_config or 'group' in i_config:
                        small_vlan.update({
                            'type': vlan_config.get('type', 'access'),
                        })

                        if 'ids' in vlan_config:
                            small_vlan.update({
                                'ids': vlan_config['ids']
                            })

                    else:
                        log.warning(f'Ignoring incomplete VLAN configuration on interface {interface}')

                if 'mtu' in i_config:
                    log.debug(f'Processing MTU on interface {interface}')
                    small_if.update({'mtu': i_config['mtu']})

                if 'addresses' in i_config:
                    log.debug(f'Processing IP addresses on interface {interface}')
                    if not 'inet' in small_if:
                        small_u0.update({'inet': {'addresses': []}, 'inet6': {'addresses': []}})
                    for address in i_config['addresses']:
                        match type(ipaddress.ip_address(address.split('/')[0])):
                            case ipaddress.IPv4Address:
                                small_u0['inet']['addresses'].append(address)
                            case ipaddress.IPv6Address:
                                small_u0['inet6']['addresses'].append(address)

    def compile_vlans():
        for vlan, vlan_config in data.get('vlans', {}).items():
            v_id = vlan_config.get('id')
            v_description = vlan_config.get('description')

            log.debug(f'Processing VLAN {vlan} with ID {v_id}')

            for group in vlan_config.get('groups', []):
                log.debug(f'Processing group: {group}')

                if group in port_groups:
                    for device, d_members in port_groups[group].items():
                        #g_description = group_config.get('description')

                        #if v_id in small_pillar[group]

                        small_device = small_pillar[device]
                        small_vlans = small_device['vlans']
                        small_ignores = small_device['ignore']['interfaces']
                        small_interfaces = small_device['interfaces']

                        if not vlan in small_vlans:
                            small_vlans[vlan] = {
                                    'description': v_description,
                                    'id': v_id
                                }

                        for interface in d_members:
                            if interface in small_ignores:
                                _fail(f'Attempted to configure interface {interface}, but it is set to be ignored. This should not happen?')

                            create_interface(interface, small_interfaces)

                            tagged = small_pillar[device]['interfaces'][interface]['units'][0]['vlan']['ids']
                            if v_id not in tagged:
                                tagged.append(v_id)

    def cleanup():
        for device, d_config in small_pillar.items():
            for interface, i_config in d_config.get('interfaces', {}).items():
                u_config = i_config.get('units', {}).get(0, {})
                v_config = u_config.get('vlan', {})

                v_config_ids = v_config.get('ids', [])
                if not 'type' in v_config and not v_config_ids:
                    log.debug(f'Purging VLAN from interface {interface}')
                    del small_pillar[device]['interfaces'][interface]['units'][0]['vlan']
                elif not v_config_ids:
                    log.debug(f'Purging VLAN ID\'s from interface {interface}')
                    del small_pillar[device]['interfaces'][interface]['units'][0]['vlan']['ids']
                if not any([k in u_config for k in ['description', 'inet', 'inet6', 'vlan']]):
                    log.debug(f'Purging unit from interface {interface}')
                    del small_pillar[device]['interfaces'][interface]['units']

    compile_devices()
    compile_vlans()
    cleanup()

    big_pillar.update(small_pillar)

    return big_pillar

def main():
    data = {}

    for category, file in {'switching': infile_s, 'devices': infile_d}.items():
        if not pathlib.Path(file).is_file():
            _fail(f'Unable to locate "{file}"')

        with open(file) as fh:
            data.update({category: yaml.safe_load(fh)})

    pillar = generate(data['switching'], data['devices'])

    for device, pillar in pillar.items():
        with open(f'{outdir}/{device}.sls', 'w') as fh:
            yaml.dump({'juniper_junos': pillar}, fh)

    log.info('ok')

#with open('sample-input.yaml', 'r') as fh:
#    data = yaml.safe_load(fh)

if __name__ == '__main__':
    log = logging.getLogger()
    log.setLevel(log_choices_converter[args.log])
    log.addHandler(logging.StreamHandler(sys.stdout))
    log.debug(args)
    #out = generate(data, {'switches': {'prg2-ibs-tor2-h02': {'role': 'access'}, 'FOO': {'role': 'access'}}})
    #print(out)
    main()
