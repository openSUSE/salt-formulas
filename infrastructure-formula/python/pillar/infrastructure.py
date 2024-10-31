"""
Copyright (C) 2024 Georg Pfuetzenreuter <mail+opensuse@georg-pfuetzenreuter.net>

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

from yaml import safe_load

root = '/srv/salt-git/pillar'

log = getLogger(__name__).debug

def generate_infrastructure_pillar(enabled_domains):
    pillar = {
        'infrastructure': {
            'domains': {},
        }
    }

    for domain in enabled_domains:
        pillar['infrastructure']['domains'][domain] = {
            'clusters': {},
            'machines': {},
        }

        domainpillar = pillar['infrastructure']['domains'][domain]
        domaindir = f'{root}/domain/'
        mydomaindir = f'{domaindir}{domain.replace(".", "_")}'

        msg = f'Parsing domain {domain}'
        log(f'{msg} ...')

        domaindata = {
                'clusters': {},
                'hosts': {},
                'inherited_clusters': {},
        }

        for file in ['clusters', 'hosts']:
            with open(f'{mydomaindir}/{file}.yaml') as fh:
                domaindata[file] = safe_load(fh)

        for cluster, clusterconfig in domaindata['clusters'].items():
            log(f'{msg} => cluster {cluster} ...')

            if 'delegate_to' in clusterconfig:
                delegated_domain = clusterconfig['delegate_to']

                with open(f'{domaindir}/{delegated_domain}/clusters.yaml') as fh:
                    domaindata['inherited_clusters'].update({
                        delegated_domain: safe_load(fh),
                    })

                if cluster in domaindata['inherited_clusters']:
                    clusterconfig = domaindata['inherited_clusters'][cluster]
                else:
                    log(f'Delegation of cluster {cluster} to {delegated_domain} is not possible!')

            clusterpillar = {
                    'storage': clusterconfig['storage'],
            }

            if 'primary_node' in clusterconfig:
                clusterpillar['primary'] = clusterconfig['primary_node']

            if 'netapp' in clusterconfig:
                clusterpillar.update({
                    'netapp': clusterconfig['netapp'],
                })

            log(clusterpillar)
            domainpillar['clusters'][cluster] = clusterpillar

        for host, hostconfig in domaindata['hosts'].items():
            log(f'{msg} => host {host} ...')

            hostpillar = {
                    'cluster': hostconfig['cluster'],
                    'disks': hostconfig.get('disks', {}),
                    'extra': {
                        'legacy': hostconfig.get('legacy_boot', False),
                    },
                    'image': hostconfig.get('image', 'admin-minimal-latest'),
                    'interfaces': {},
                    'ram': hostconfig['ram'],
                    'vcpu': hostconfig['vcpu'],
            }

            if 'node' in hostconfig:
                node = hostconfig['node']

                # the node key is compared against the hypervisor minion ID, which is always a FQDN in our infrastructure
                if '.' in node:
                    hostpillar['node'] = node
                else:
                    hostpillar['node'] = f'{node}.{domain}'

            hostinterfaces = hostconfig.get('interfaces', {})

            ip4 = hostconfig.get('ip4')
            ip6 = hostconfig.get('ip6')

            if not ip4 and not ip6 and hostinterfaces:
                if 'primary_interface' in hostconfig:
                    interface = hostconfig['primary_interface']
                elif len(hostinterfaces) == 1:
                    interface = next(iter(hostinterfaces))
                else:
                    interface = 'eth0'

                if interface in hostinterfaces:
                    ip4 = hostinterfaces[interface].get('ip4')
                    ip6 = hostinterfaces[interface].get('ip6')

            hostpillar['ip4'] = ip4
            hostpillar['ip6'] = ip6

            for interface, ifconfig in hostinterfaces.items():
                iftype = ifconfig.get('type', 'direct')

                ifpillar = {
                        'mac': ifconfig['mac'],
                        'type': iftype,
                        'source': ifconfig['source'] if 'source' in ifconfig else f'x-{interface}',
                }

                if iftype == 'direct':
                    ifpillar['mode'] = ifconfig.get('mode', 'bridge')

                for i in [4, 6]:
                    ipf = f'ip{i}'

                    if ipf in ifconfig:
                        ifpillar[ipf] = ifconfig[ipf]

                hostpillar['interfaces'][interface] = ifpillar

            log(hostpillar)
            domainpillar['machines'][host] = hostpillar

    return pillar
