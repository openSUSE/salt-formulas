"""
Copyright (C) 2024-2025 SUSE LLC <georg.pfuetzenreuter@suse.com>

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

from .common import pillar_domain_path

from bisect import insort
from ipaddress import ip_network
from logging import getLogger
from pathlib import PosixPath

import yaml

log = getLogger(__name__)

def generate_juniper_junos_pillar(enabled_domains, minion_id, spacemap):
    minion = minion_id.replace('LAB-', '')
    data = {'networks': {}, 'switching': {}}
    config = {}
    log.debug('Starting juniper_junos pillar construction ...')

    minion_s = minion.split('-')
    if len(minion_s) != 4:
        log.error('Cannot parse minion ID')
        return {}
    space = minion_s[1].lower()
    log.debug(f'Minion space set to "{space}"')

    for domain in enabled_domains:
        domain_space = domain.split('.')[0]
        if domain_space in spacemap:
            domain_space = spacemap[domain_space]
        log.debug(f'Domain space set to "{domain_space}"')

        for dataset in data.keys():
            log.debug(f'Scanning domain {domain}, dataset {dataset} ...')
            file = pillar_domain_path(domain) + '/' + dataset + '.yaml'

            if PosixPath(file).is_file():
                with open(file) as fh:

                    if dataset == 'switching':
                        log.debug('Updating data ...')
                        data[dataset].update(yaml.safe_load(fh))

                    elif dataset == 'networks':
                        log.debug('Not updating data, scanning networks ...')
                        for network, nwconfig in yaml.safe_load(fh).items():
                            done = False

                            for existing_network, existing_nwconfig in data[dataset].items():
                                if network == existing_network or nwconfig.get('id') == existing_nwconfig.get('id'):
                                    mynetwork = existing_network
                                    log.debug(f'Mapping network {network} to existing network {mynetwork}')

                                    if nwconfig.get('description') != data[dataset][mynetwork].get('description'):
                                        log.warning(f'Conflicting descriptions in network {mynetwork}')
                                    if nwconfig.get('id') != data[dataset][mynetwork].get('id'):
                                        log.error(f'Conflicting ID: {network} != {mynetwork}, refusing to continue!')
                                        return {}

                                    if 'groups' not in data[dataset][mynetwork]:
                                        data[dataset][mynetwork]['groups'] = []
                                    for group in nwconfig.get('groups', []):
                                        insort(data[dataset][mynetwork]['groups'], group)

                                    done = True
                                    break

                            if not done:
                                if space == domain_space:
                                    log.debug(f'Creating new network {network}')
                                    data[dataset][network] = nwconfig
                                else:
                                    log.debug(f'Ignoring network {network}')

            else:
                log.warning(f'File {file} does not exist.')

    if minion in data['switching']:
        config.update(data['switching'][minion])
    else:
        return {}

    log.debug(f'Constructing juniper_junos pillar for {minion}')

    vlids = []
    groups = {}
    for interface, ifconfig in config.get('interfaces', {}).items():
        log.debug(f'Parsing interface {interface} ...')
        for vlid in ifconfig.get('vlan', {}).get('ids', []):
            if vlid not in vlids:
                vlids.append(vlid)

        group = None
        if 'group' in ifconfig:
            group = ifconfig['group']
        elif 'addresses' in ifconfig:
            group = '__lonely'
        elif 'vlan' in ifconfig and 'all' in ifconfig['vlan'].get('ids', []):
            group = '__all'
        if group:
            if group not in groups:
                groups.update({group: {'interfaces': [], 'networks': []}})  # noqa 206
            log.debug(f'Appending interface {interface} to group {group}')
            groups[group]['interfaces'].append(interface)

    group_names = groups.keys()

    for network, nwconfig in data['networks'].items():
        matching_groups = [group for group in nwconfig.get('groups', []) if group in group_names]

        if nwconfig['id'] in vlids or any(matching_groups) or network.startswith(('ICCL_', 'ICCP_')):
            log.debug(f'Adding network {network} to config ...')
            if 'vlans' not in config:
                config.update({'vlans': {}})
            if network not in config['vlans']:
                config['vlans'].update({network: {}})
            config['vlans'][network].update({'id': nwconfig['id']})
            if 'description' in nwconfig:
                config['vlans'][network].update({'description': nwconfig['description']})
            for group in matching_groups:
                groups[group]['networks'].append(network)

    for group, members in groups.items():
        for interface in members['interfaces']:
            ifconfig = config['interfaces'][interface]

            unit = 0
            if '.' in interface:
                ifsplit = interface.split('.')
                ifname = ifsplit[0]
                ifsuffix = ifsplit[1]
                if ifsuffix.isdigit():
                    unit = int(ifsuffix)

            if 'units' not in ifconfig:
                ifconfig.update({'units': {}})
            if unit not in ifconfig['units']:
                ifconfig['units'].update({unit: {}})
            if members['networks']:
                ifconfig['units'][unit].update({'vlan': {'ids': [], 'type': ifconfig.get('vlan', {}).get('type', 'access')}})  # noqa 206
            for network in members['networks']:
                if config['vlans'][network]['id'] not in ifconfig['units'][unit]['vlan']['ids']:
                    insort(ifconfig['units'][unit]['vlan']['ids'], config['vlans'][network]['id'])
            if 'addresses' in ifconfig:
                for address in ifconfig['addresses']:
                    address_version = ip_network(address, False).version
                    if address_version == 4:
                        family = 'inet'
                    elif address_version == 6:
                        family = 'inet6'
                    else:
                        log.error(f'Illegal address: {address}')
                    if family not in ifconfig['units'][unit]:
                        ifconfig['units'][unit].update({family: {'addresses': []}})  # noqa 206
                    ifconfig['units'][unit][family]['addresses'].append(address)
                del ifconfig['addresses']
            elif group == '__all':
                ifconfig['units'][unit].update({'vlan': {'ids': ['all'], 'type': ifconfig.get('vlan', {}).get('type', 'trunk')}})  # noqa 206
            if unit > 0:
                config['interfaces'][ifname] = config['interfaces'].pop(interface)

    log.debug(f'Returning juniper_junos pillar for {minion}: {config}')
    return {'juniper_junos': config}
