"""
Copyright (C) 2024-2025 Georg Pfuetzenreuter <mail+opensuse@georg-pfuetzenreuter.net>

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

from logging import getLogger

from .common import pillar_domain_data

log = getLogger(__name__).debug

def generate_network_pillar(enabled_domains, domain, host, site=None):
    if domain not in enabled_domains:
        return {}

    msg = f'common.network, host {host}:'

    domaindata = pillar_domain_data(domain, [
            'hosts',
            'networks',
        ],
        site,
    )

    # machine not in hosts, can be an error or expected (for example because the machine is bare metal or in an unsupported location)
    if host not in domaindata['hosts']:
        return {}

    pillar = {}

    hostconfig = domaindata['hosts'][host]
    ifconfig   = hostconfig.get('interfaces', {})

    if 'primary_interface' in hostconfig:
        primary_interface = hostconfig['primary_interface']

    elif len(ifconfig) == 1:
        primary_interface = next(iter(ifconfig))

    else:
        interface_candidates = [interface for interface in ifconfig.keys() if not interface.endswith('-ur')]

        if len(interface_candidates) > 0:
            primary_interface = next(iter(interface_candidates))

        else:
            primary_interface = 'eth0'

    log(f'{msg} primary interface set to {primary_interface}')

    if primary_interface in ifconfig and ( 'ip4' in ifconfig[primary_interface] or 'ip6' in ifconfig[primary_interface] ):
        ip4 = ifconfig[primary_interface].get('ip4')
        ip6 = ifconfig[primary_interface].get('ip6')

        # if an interface name contains a hyphen, it can be assumed to match our short VLAN nameing convention
        if '-' in primary_interface:
            shortnet = primary_interface

        # alternatively assess the network segment based off the source (hypervisor) interface
        else:
            shortnet = ifconfig[primary_interface].get('source', '').replace('x-', '')

        log(f'{msg} shortnet set to {shortnet}')

    # if no primary interface is available, find and apply addresses defined outside of an "interfaces" block (single interface hosts might use this)
    else:
        log(f'{msg} trying to use generic interface addresses')
        ip4 = hostconfig.get('ip4')
        ip6 = hostconfig.get('ip6')
        ifconfig = {}
        shortnet = None

    ifconfig.pop(primary_interface, None)

    log(f'{msg} primary IPv4 address set to {ip4}')
    log(f'{msg} primary IPv6 address set to {ip6}')

    if ip4 is not None or ip6 is not None or ifconfig:
        pillar['network'] = {}

        pillar['network']['interfaces'] = {}

        if ip4 is not None or ip6 is not None:
            pillar['network']['interfaces'][primary_interface] = {
                    'addresses': [],
            }
            addresses = pillar['network']['interfaces'][primary_interface]['addresses']

            if ip4 is not None:
                addresses.append(ip4)

            if ip6 is not None:
                addresses.append(ip6)

            # firewall is managed through the firewalld pillar, avoid conflict with the wicked firewalld integration
            pillar['network']['interfaces'][primary_interface]['firewall'] = False

        for add_interface, add_ifconfig in ifconfig.items():
            if 'ip4' in add_ifconfig or 'ip6' in add_ifconfig:
                log(f'{msg} configuring additional interface {add_interface}')
                pillar['network']['interfaces'][add_interface] = {
                        'addresses': [],
                }
                add_addresses = pillar['network']['interfaces'][add_interface]['addresses']

                if 'ip4' in add_ifconfig:
                    add_addresses.append(add_ifconfig['ip4'])

                if 'ip6' in add_ifconfig:
                    add_addresses.append(add_ifconfig['ip6'])

                # explanation above
                pillar['network']['interfaces'][add_interface]['firewall'] = False

    if shortnet:
        for network, nwconfig in domaindata['networks'].items():
            if network == shortnet or nwconfig.get('short') == shortnet:
                longnet = network
                break
        else:
            longnet = None

        log(f'{msg} network set to {longnet}')

        if longnet:
            nwconfig = domaindata['networks'][network]

            if 'gw4' in nwconfig or 'gw6' in nwconfig:
                pillar['network']['routes'] = {}

                if ip4 is not None and 'gw4' in nwconfig:
                    if isinstance(nwconfig['gw4'], dict) and 'gw_vip' in nwconfig['gw4']:
                        gw4 = nwconfig['gw4']['gw_vip']
                    else:
                        gw4 = nwconfig['gw4']

                    pillar['network']['routes']['default4'] = {
                            'gateway': gw4,
                    }

                if ip6 is not None and 'gw6' in nwconfig:
                    pillar['network']['routes']['default6'] = {
                            'gateway': nwconfig['gw6'],
                    }

    return pillar
