#!/usr/bin/python3
"""
Tool converting Junos "set" output to our YAML configuration format for use with Salt
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
import json
import yaml
import pathlib
import re
import sys

argparser = argparse.ArgumentParser()
argparser.add_argument('--in-file', type=str, default='input.txt')
argparser.add_argument('--in-dir')
argparser.add_argument('--out-file', type=str, default='output.yaml')
argparser.add_argument('--out-dir', type=str)
args = argparser.parse_args()

if args.in_file != 'input.txt' and args.in_dir or args.out_file != 'output.yaml' and args.out_dir:
    print('Cannot use file and directory operation at once')
    sys.exit(1)

if args.in_dir and args.out_dir:
    infiles = mylist = [file.absolute().as_posix() for file in pathlib.Path(args.in_dir).glob('*.SET')]
    outdir = args.out_dir
    if not pathlib.Path(outdir).is_dir():
        print('Output directory does not exist')
        sys.exit(1)
    outfile = None
elif args.in_file and args.out_file:
    infiles = [args.in_file]
    outdir = None
    outfile = args.out_file

discard = ['mtu']
lacp_key = 'lacp'
mclag_key = 'mc'

def do_description(description):
    return 'description', ' '.join(description).replace('"','')

def calculate(file):
    confmap = {'applications': {}, 'interfaces': {}, 'subinterfaces': {}, 'zones': {}, 'addresses': {}, 'address_sets': {}, 'policies': [], 'snats': {}, 'proxyarps': {}, 'snat_rules': {}, 'static_nat_rules': {}, 'sroutes': [], 'sroutes6': []}
    outmap = {'services': [], 'interfaces': {}, 'zones': [], 'addresses': [], 'address_groups': [], 'policies': [], 'source_nat_pools': [], 'proxy_arp': [], 'source_nat_rules': [], 'static_nat_rules': [], 'sroutes': [], 'sroutes6': [], 'vlans': {}}
    with open(file, 'r') as fh:
        print(file)
        for line in fh:
            ls = line.replace('\n', '').split(' ')
            lsl = len(ls)
            if lsl < 5:
                continue
            match ls[1]:
                case 'applications':
                    name = ls[3]
                    if not name in confmap['applications']:
                        confmap['applications'].update({name: {}})
                    confmap['applications'][name].update({ls[4]: ls[5]})
                case 'interfaces':
                    name = ls[2]
                    if not name in confmap['interfaces']:
                        confmap['interfaces'].update({name: {}})
                    mymap = confmap['interfaces'][name]
                    if ls[3] == 'unit':
                        unit = int(ls[4])
                        #if not 'units' in mymap:
                        #    mymap.update({'units': {}})
                        #myunits = mymap['units']
                        #if not unit in myunits:
                        #    myunits.update({unit: {}})
                        #    myunit = myunits[unit]
                        if unit == 0:
                            print(ls)
                            if lsl > 5:
                                match ls[5]:
                                    case 'family':
                                        if ls[6] == 'ethernet-switching' and lsl > 7 and ls[7] in ['vlan', 'interface-mode']:
                                            #print('found vlan')
                                            #if not 'vlan' in myunit:
                                            #    myunit.update({'vlan': {}})
                                            #myvlan = myunit['vlan']
                                            if not 'vlan' in mymap:
                                                mymap.update({'vlan': {}})
                                            myvlan = mymap['vlan']
                                            if ls[8] == 'members':
                                                if not 'ids' in myvlan:
                                                    myvlan['ids'] = []
                                                myvlan['ids'].append(ls[9])
                                            elif ls[7] == 'interface-mode':
                                                print('found imode ')
                                                myvlan['type'] = ls[8]
                        # currently neither needed nor supported by the configuration
                        #elif unit != 0:
                        #    name = f'{name}.{ls[4]}'
                        #    if not name in confmap['subinterfaces']:
                        #        confmap['subinterfaces'].update({name: {}})
                        #    mymap = confmap['subinterfaces'][name]
                    mykey, myval = None, None
                    if ls[3] == 'description':
                        mykey, myval = do_description(ls[4:])
                    elif ls[3] == 'mtu':
                        mymap['mtu'] = int(ls[4])
                    elif lsl >= 7 and ls[5] == 'description':
                        mykey, myval = do_description(ls[6:])
                    elif lsl == 6 or (lsl == 7 and ls[4] == 'lacp') or (lsl == 7 and ls[4] == 'mc-ae'):
                        mykey, myval = ls[4], ls[5]
                        match mykey:
                            case 'redundancy-group':
                                # set interfaces reth0 redundant-ether-options redundancy-group 1
                                mykey = lacp_key
                                myval = {'group': int(myval)}
                            case 'lacp':
                                mykey = lacp_key
                                if lsl == 6:
                                    # set interfaces reth0 redundant-ether-options lacp active
                                    myval = {'mode': myval}
                                elif lsl == 7:
                                    # set interfaces reth0 redundant-ether-options lacp periodic fast
                                    myval = {ls[5]: ls[6]}
                            case 'mc-ae':
                                mykey = mclag_key
                                myval = {ls[5]: ls[6]}
                            case '802.3ad':
                                mykey = 'lag'
                                myval = ls[5]
                    elif lsl == 9:
                        if ls[3] == 'unit':
                            myval = ls[8]
                            match ls[6]:
                                case 'inet':
                                    # set interfaces reth0 unit 0 family inet address 195.135.223.5/28
                                    #mykey = 'addr'
                                    mykey = 'addresses'
                                case 'inet6':
                                    # set interfaces reth0 unit 0 family inet6 address 2a07:de40:b260:0001::5/64
                                    #mykey = 'addr6'
                                    mykey = 'addresses'
                    elif lsl == 5:
                        mykey, myval = ls[3], ls[4]
                    #else:
                        #print(f'Dropped line: {ls}')
                    if mykey and myval:
                        #print(mykey)
                        if mykey in ['lacp', 'mc']:# and lsl > 6:
                            if not 'ae' in mymap:
                                mymap['ae'] = {}
                            myae = mymap['ae']
                            lowmap = myae
                        else:
                            lowmap = mymap
                        if mykey == 'lag':
                            mykey = lacp_key
                        if mykey in lowmap:
                            #print(myval)
                            #print(mykey)
                            if isinstance(myval, dict):
                                # add to existing lacp_options
                                lowmap[mykey].update(myval)
                            elif isinstance(myval, str) and isinstance(mykey, str):
                                lowmap[mykey] = myval
                            elif isinstance(mykey[mykey], list):
                                lowmap[mykey].append(myval)
                        elif mykey not in discard:
                            if mykey.startswith('addr'):
                                myval = [myval]
                            lowmap.update({mykey: myval})
                case 'security':
                    if ls[3] == 'security-zone':
                        name = ls[4]
                        if not name in confmap['zones']:
                            confmap['zones'].update({name: {'interfaces': [], 'local-services': []}})
                        match ls[5]:
                            case 'interfaces':
                                ifname = ls[6]
                                iflist = confmap['zones'][name]['interfaces']
                                if not ifname in iflist:
                                    iflist.append(ifname)
                            case 'host-inbound-traffic':
                                svname = ls[7]
                                svlist = confmap['zones'][name]['local-services']
                                if not svname in svlist:
                                    svlist.append(svname)
                    elif ls[2] == 'address-book':
                        name = ls[5]
                        match ls[4]:
                            case 'address':
                                addressmap = confmap['addresses']
                                address = ' '.join(ls[6:])
                                addressmap.update({name: address})
                            case 'address-set':
                                addressmap = confmap['address_sets']
                                if not name in addressmap:
                                    addressmap.update({name: []})
                                addressmap[name].append(ls[7])
                    elif ls[2] == 'policies':
                        #if ls[7] == 'policy':
                        #    policy = ls[8]
                        #if policy not in confmap['policies']:
                        #    confmap['policies'].update({policy: {'match': {'sources': [], 'destinations': [], 'applications': []}}})
                        #policymap = confmap['policies'][policy]
                        policymap = confmap['policies']

                        mymap = {'match': {'sources': [], 'destinations': [], 'applications': []}}

                        if ls[7] == 'policy':
                            policy = ls[8]
                            mymap.update({'name': policy})
                        if ls[3] == 'from-zone':
                            from_zone = ls[4]
                            mymap.update({'from_zone': from_zone})
                        if ls[5] == 'to-zone':
                            to_zone = ls[6]
                            mymap.update({'to_zone': to_zone})
                        if ls[9] == 'match':
                            match ls[10]:
                                case 'source-address':
                                    source = ls[11]
                                    mymap['match']['sources'].append(source)
                                case 'destination-address':
                                    destination = ls[11]
                                    mymap['match']['destinations'].append(destination)
                                case 'application':
                                    application = ls[11]
                                    mymap['match']['applications'].append(application)
                        elif ls[9] == 'then':
                            mymap.update({'action': ls[10]})

                        policymap.append(mymap)

                    elif ls[2] == 'nat':
                        if ls[3] in ['source', 'static']:
                            name = ls[5]
                            if ls[4] == 'pool':
                                if ls[6] == 'address':
                                    address = ls[7]
                                    confmap['snats'].update({name: address})
                            elif ls[4] == 'rule-set':
                                if ls[3] == 'source':
                                    confname = 'snat_rules'
                                elif ls[3] == 'static':
                                    confname = 'static_nat_rules'
                                rulesetmap = confmap[confname]
                                if not name in rulesetmap:
                                    rulesetmap.update({name: {'rules': {}}})
                                if ls[6] in ['from', 'to'] and ls[7] == 'zone':
                                    rulesetmap[name].update({ls[6]: ls[8]})
                                if ls[6] == 'rule':
                                    rulename = ls[7]
                                    if not rulename in rulesetmap[name]['rules']:
                                        rulesetmap[name]['rules'].update({rulename: {'sources': [], 'destinations': []}})
                                    rulemap = rulesetmap[name]['rules'][rulename]
                                    if ls[8] == 'match' and ls[9] == 'source-address':
                                        rulemap['sources'].append(ls[10])
                                    if ls[8] == 'match' and ls[9] == 'destination-address':
                                        # we don't seem to use this and assume everything?
                                        rulemap['destinations'].append(ls[10])
                                    elif ls[8] == 'then':
                                        if ls[9] == 'source-nat':
                                            if ls[10] == 'pool':
                                                rulemap.update({'pool': ls[11]})
                                        elif ls[9] == 'static-nat':
                                            if ls[10] == 'prefix':
                                                rulemap.update({'prefix': ls[11]})
                                    if not rulemap['destinations']:
                                        # feels wrong, it's in the expected output file but not in the input file
                                        rulemap['destinations'].append('0.0.0.0/0')

                        elif ls[3] == 'proxy-arp':
                            if ls[4] == 'interface' and ls[6] == 'address':
                                interface = ls[5]
                                address = ls[7]
                                confmap['proxyarps'].update({interface: address})

                case 'routing-options':
                    if ls[2] == 'static' and ls[3] == 'route' and ls[5] == 'next-hop':
                        route = ls[4]
                        hop = ls[6]
                        confmap['sroutes'].append({'dst': route, 'gw': hop})
                    elif ls[2] == 'rib' and ls[3] == 'inet6.0' and ls[4] == 'static' and ls[5] == 'route' and ls[7] == 'next-hop':
                        route = ls[6]
                        hop = ls[8]
                        confmap['sroutes6'].append({'dst': route, 'gw': hop})

                case 'vlans':
                    vlan = ls[2]
                    match ls[3]:
                        case 'vlan-id':
                            mykey = 'id'
                            myval = int(ls[4])
                        case 'description':
                            mykey, myval = do_description(ls[4:])
                    mymap = outmap['vlans']
                    if vlan in mymap:
                        mymap[vlan].update({mykey: myval})
                    else:
                        mymap.update({vlan: {mykey: myval}})

    scrubbed_policies = []
    for policy in confmap['policies']:
        scrubbed = policy.copy()
        scrubbed.pop('match')
        if 'action' in scrubbed:
            scrubbed.pop('action')
        scrubbed_policies.append(scrubbed)

    unique_policies = [dict(t) for t in {tuple(d.items()) for d in scrubbed_policies}]

    for policy in unique_policies:
        policymap = {'fromzn': policy['from_zone'], 'tozn': policy['to_zone'], 'name': policy['name'], 'srcs': [], 'dsts': [], 'applications': []}
        for origpolicy in confmap['policies']:
            if origpolicy['name'] == policy['name'] and origpolicy['from_zone'] == policy['from_zone'] and origpolicy['to_zone'] == policy['to_zone']:
                new_sources = set(origpolicy['match']['sources']) - set(policymap['srcs'])
                if new_sources:
                    policymap['srcs'].extend(list(new_sources))
                new_destinations = set(origpolicy['match']['destinations']) - set(policymap['dsts'])
                if new_destinations:
                    policymap['dsts'].extend(list(new_destinations))
                new_applications = set(origpolicy['match']['applications']) - set(policymap['applications'])
                if new_applications:
                    policymap['applications'].extend(list(new_applications))
                if 'action' in origpolicy:
                    policymap.update({'action': origpolicy['action']})
        if not policymap['srcs']:
            del policymap['srcs']
        if not policymap['dsts']:
            del policymap['dsts']
        if not policymap['applications']:
            del policymap['applications']
        outmap['policies'].append(policymap)

    for config in confmap.keys():
        if isinstance(confmap[config], list):
            if not config == 'policies':
                # currently used for sroutes and sroutes6
                outmap[config].extend(confmap[config])
            continue
        for name, lowconfig in confmap[config].items():
            match config:
                case 'applications':
                    outport = lowconfig.get('destination-port', 'N/A')
                    try:
                        outport = int(outport)
                    except ValueError:
                        outport = outport
                    outconfig = {'name': name, 'proto': lowconfig['protocol'], 'port': outport}
                    outmap['services'].append(outconfig)
                case 'interfaces':
                    outmap['interfaces'].update({name: lowconfig})
                #case 'subinterfaces':
                #    mymap = {'ifname': name}
                #    mymap.update(lowconfig)
                #    mymap.update({'vlanid': int(re.search(r'\d+$', name).group(0))})
                #    outmap['subinterfaces'].append(mymap)
                case 'zones':
                    mymap = {'name': name}
                    mymap.update(lowconfig)
                    outmap['zones'].append(mymap)
                case 'addresses':
                    mymap = {'name': name, 'prefix': lowconfig}
                    outmap['addresses'].append(mymap)
                case 'address_sets':
                    mymap = {'name': name, 'addresses': lowconfig}
                    outmap['address_groups'].append(mymap)
                # policies are now treated in a special clinic
                #case 'policies':
                #    match = lowconfig['match']
                #    mymap = {'fromzn': lowconfig['from_zone'], 'tozn': lowconfig['to_zone'], 'name': name,
                #             'srcs': match['sources'], 'dsts': match['destinations'], 'applications': match['applications'],
                #             'action': lowconfig['action']}
                #    outmap['policies'].append(mymap)
                case 'snats':
                    mymap = {'name': name, 'prefix': lowconfig}
                    outmap['source_nat_pools'].append(mymap)
                case 'proxyarps':
                    mymap = {'interface': name, 'prefix': lowconfig}
                    outmap['proxy_arp'].append(mymap)
                case 'snat_rules':
                    mymap = {'set': name, 'fromzn': lowconfig['from'], 'tozn': lowconfig['to'], 'rules': []}
                    for rule, ruleconfig in lowconfig['rules'].items():
                        mymap['rules'].append({'name': rule, 'srcs': ruleconfig['sources'], 'dsts': ruleconfig['destinations'], 'pool': ruleconfig['pool']})
                    outmap['source_nat_rules'].append(mymap)
                case 'static_nat_rules':
                    mymap = {'set': name, 'fromzn': lowconfig['from'], 'rules': []}
                    for rule, ruleconfig in lowconfig['rules'].items():
                        thismap = {'name': rule, 'dsts': ruleconfig['destinations'], 'natprefix': ruleconfig['prefix']}
                        if ruleconfig['sources']:
                            # we don't seem to use this
                            thismap.update({'srcs': ruleconfig['sources']})
                        mymap['rules'].append(thismap)
                    outmap['static_nat_rules'].append(mymap)

    return outmap

#with open('debug', 'w') as fh:
#    json.dump(confmap, fh)


for file in infiles:
    outmap = calculate(file)
    filename = pathlib.Path(file).with_suffix("").name
    print(filename)

    dumpmap = {}
    dumpmap['devices'] = {filename: {}}
    dd = dumpmap['devices'][filename]


    for key, value in outmap.items():
        if key:
            pair = {key: value}
            # to-do: maybe differentiate between switching and firewall keys?
            if key in ['vlans']:
                dumpmap.update(pair)
            elif key in ['interfaces']:
                dd.update(pair)

    if not dd:
        dumpmap.clear()

    ## why is it "output" if using --out-dir ?
    if outdir: #and not outfile:
        outfile = f'{outdir}/{filename}.yaml'

    #print(dumpmap)
    #print(outfile)

    with open(outfile, 'w') as fh:
    #    yaml.Dumper.ignore_aliases = lambda *args : True
        yaml.dump(dumpmap, fh, sort_keys=False)
