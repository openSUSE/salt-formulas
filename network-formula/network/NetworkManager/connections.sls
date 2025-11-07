#!py
# vim: ft=python ts=2 sts=2 sw=2
"""
Salt state file for managing NetworkManager connections
Copyright (C) 2025 Georg Pfuetzenreuter <mail+opensuse@georg-pfuetzenreuter.net>

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

from ipaddress import ip_address, ip_network
from logging import getLogger
from uuid import uuid4

from gi.repository import GLib

log = getLogger('salt.network-formula.NMInterfaces')

DEFAULTS = {
    'ipv6': {
      # default in nmcli as well
      'addr-gen-mode': 'default',
    },
}

# Translation from ifcfg to NetworkManager options
# - dict keys define ifcfg keys
# - empty dicts as value indicate the option is to be skipped
# - bonding_module_opts bonding_slave* are translated in separate logic
IFCFG_NM_TRANS = {
    'bridge_ports': {},
    'bonding_master': {},
    'usercontrol': {},
    'bootproto': {
      'section': 'ipv',  # gets expanded to ipv4/ipv6
      'name': 'method',
      'values': {
        'auto6': 'auto',
        'autoip': 'auto',
        'dhcp': 'auto',
        'dhcp+autoip': 'auto',
        'dhcp4': 'auto',
        'dhcp6': 'auto',
        'none': 'disabled',
        'static': 'manual',
      },
    },
    'startmode': {
      'section': 'connection',
      'name': 'autoconnect',
      'values': {
        'auto': True,
        'manual': False,
        'off': False,
        'no': False,
      },
    },
    'interfacetype': {
      'section': 'connection',
      'name': 'type',
      # TODO: verify if all values are the same
    },
    'firewall': {
      'section': 'connection',
      'name': 'zone',
      'values': {
        'no': 'SKIP',
      },
    },
}

SINGULARS = {
    'addresses': 'address',
    'routes': 'route',
}

def _translate_generic(option, value):
  # returns: section (str), option (str), value (str), skip (bool)

  if IFCFG_NM_TRANS[str(option)]:
    log.warn(f'Processing legacy option "{option}".')
  else:
    log.warn(f'Skipping legacy option "{option}".')
    return None, None, None, True

  new_option = IFCFG_NM_TRANS[option]['name']
  new_value = IFCFG_NM_TRANS[option].get('values', {}).get(value, value)

  if new_value == 'SKIP':
    log.warn(f'Skipping legacy option "{option}" due to value.')
    return None, None, None, True

  if new_value is None:
    log.error(f'Unable to translate "{option}={value}".')
    return None, None, None, True

  section = IFCFG_NM_TRANS[option]['section']

  log.warn(f'Translated legacy setting "{option}={value}" to "{section}.{new_option}={new_value}".')

  return section, new_option, new_value, False

def _translate_split(value):
  # returns: expanded key/values (dict)

  out = {}

  for pair in value.split():
    k, v = pair.split('=')

    out[k] = v

  return out

def run():
  states = {}

  jmap = __salt__['cp.cache_file']('salt://network/NetworkManager/map.jinja')
  settings = {
      setting: __salt__['jinja.load_map'](jmap, setting)
      for setting in [
        'base',
        'base_backup',
        'control',
        'interfaces',
        'routes',
        'script',
      ]
  }

  nm_data = {}
  controllers = {
      'bridge': {},
      'bond': {},
  }

  for interface, config in settings['interfaces'].items():
    nm_data[interface] = {
        'connection': {},
        'ipv4': {},
        'ipv6': {},
        # TODO: support more sections
    }

    if 'address' in config:
      addresses = config['address']
    elif 'addresses' in config:
      addresses = config['addresses']
    else:
      addresses = []

    if isinstance(addresses, str):
      addresses = [addresses]

    for address in addresses:
      v = ip_network(address, False).version

      ipv = f'ipv{v}'

      if 'addresses' not in nm_data[interface][ipv]:
        nm_data[interface][ipv]['addresses'] = []

      nm_data[interface][ipv]['addresses'].append(address)

    for option, value in config.items():
      if option in ['address', 'addresses']:
        continue

      option = option.lower()
      # TODO: keyfile supports booleans
      if value is True:
        value = 'yes'
      elif value is False:
        value = 'no'
      elif isinstance(value, str) and value != 'ethtool_options':
        value = value.lower()

      if option in IFCFG_NM_TRANS:
        section, new_option, new_value, skip = _translate_generic(option, value)

        if skip:
          continue

        if section == 'ipv':
          for ipv in ['ipv4', 'ipv6']:
            if nm_data[interface][ipv].get('addresses'):
              nm_data[interface][ipv][new_option] = new_value
        else:
          if section not in nm_data[interface]:
            nm_data[interface][section] = {}

          nm_data[interface][section][new_option] = new_value

      elif option == 'bonding_module_opts':
        log.warn(f'Processing legacy option "{option}".')

        bmo = _translate_split(value)

        if 'bond' in nm_data[interface]:
          nm_data[interface]['bond'].update(bmo)
        else:
          nm_data[interface]['bond'] = bmo

      elif option[0:13] == 'bonding_slave':
        log.warn(f'Adding bonding ports from legacy "{option}" option.')

        if interface not in controllers['bond']:
          controllers['bond'][interface] = []

        controllers['bond'][interface].append(value)

      # if the value is a dictionary, we expect it to be a native NetworkManager section

      elif option in nm_data[interface] and isinstance(value, dict):
        nm_data[interface][option].update(value)
      elif isinstance(option, dict):
        nm_data[interface][option] = value
      else:
        log.error(f'Unable to parse "{option}".')

    if 'bridge_ports' in config:
      log.warn('Adding bridge ports from legacy "bridge_ports" option.')
      if 'type' not in nm_data[interface]['connection']:
        nm_data[interface]['connection']['type'] = 'bridge'

      bridge_ports = config['bridge_ports']
      if isinstance(bridge_ports, str):
        bridge_ports = bridge_ports.split()

      controllers['bridge'][interface] = bridge_ports

  for interface, config in settings['interfaces'].items():
    for ipv in ['ipv4', 'ipv6']:
      if 'method' not in nm_data[interface][ipv]:
        if nm_data[interface][ipv].get('addresses'):
          nm_data[interface][ipv]['method'] = 'manual'
        else:
          nm_data[interface][ipv]['method'] = 'disabled'

    for section, options in DEFAULTS.items():
      for option, value in options.items():
        if option not in nm_data[interface][section]:
          nm_data[interface][section][option] = value

    if 'type' not in nm_data[interface]['connection']:
      if interface in controllers['bridge']:
        t = 'bridge'
      elif interface in controllers['bond']:
        t = 'bond'
      else:
        t = 'ethernet'

      nm_data[interface]['connection']['type'] = t

      for controller, ports in controllers['bridge'].items():
        if interface in ports:
          nm_data[interface]['connection']['port-type'] = 'bridge'
          break

  for controller_type, controller_connections in controllers.items():
    for controller, ports in controller_connections.items():
      for port in ports:
        if port in nm_data:
          log.warn(f'Setting {port} as {controller_type} member under controller {controller}.')

          nm_data[port]['connection']['port-type'] = controller_type
          nm_data[port]['connection']['controller'] = controller

        else:
          log.warn(f'Assuming {controller_type} port {port} under controller {controller}.')

          nm_data[port] = {
              'connection': {
                'type': 'ethernet',
                'port-type': controller_type,
                'controller': controller,
              },
          }

  interface_addresses = {
      'ipv4': {},
      'ipv6': {},
  }

  for interface, config in nm_data.items():
    for section, options in config.items():
      if section not in ['ipv4', 'ipv6']:
        continue

      for option, value in options.items():
        if option == 'addresses':
          interface_addresses[section][interface] = value

  for destination_network, options in settings['routes'].items():
    if 'gateway' not in options:
      continue

    if destination_network == 'default6':
      family = 'ipv6'
      destination = 'default'
    elif destination_network == 'default4':
      family = 'ipv4'
      destination = 'default'
    else:
      destination = ip_network(destination_network, False)
      family = 'ipv' + str(destination.version)

    gateway_address = options['gateway']
    gateway = ip_address(gateway_address)

    for interface, addresses in interface_addresses[family].items():
      for address in addresses:
        if gateway in ip_network(address, False):
          if destination == 'default':
            if 'gateway' in nm_data[interface][family]:
              log.warn(f'Skipping duplicate gateway definition for interface {interface}.')
            else:
              nm_data[interface][family]['gateway'] = gateway_address
          else:
            if 'routes' not in nm_data[interface][family]:
              nm_data[interface][family]['routes'] = []

            nm_data[interface][family]['routes'].append((destination_network, gateway_address))

        break

  interface_files = {}
  interface_uuids = {}

  for interface, config in nm_data.items():
    file = f'{settings["base"]}/{interface}.nmconnection'

    if __salt__['file.file_exists'](file):
      interface_files[interface] = file

      kf = GLib.KeyFile()
      kf.load_from_file(file, GLib.KeyFileFlags.NONE)

      interface_uuids[interface] = kf.get_string('connection', 'uuid')

  """
  states['network_nm_backup_directory'] = {
      'file.directory': [
        {'name': base_backup},
      ]
  }
  """

  if interface_files:
    states['network_nm_nmconnection_backup'] = {
        'file.copy': [
          {
            'names': [
              {
                f'{settings["base_backup"]}/{interface}.nmconnection': [
                  {'source': file},
                ],
              } for interface, file in interface_files.items()
            ],
          },
          {
            'require': [
              {'file': 'network_nm_backup_directory'},
            ],
          },
        ],
    }

  data = {}

  for interface, config in nm_data.items():
    kf = GLib.KeyFile()

    kf.set_comment(None, None, __salt__['pillar.get']('managed_by_salt_formula', ' This file is managed by the Salt network formula - do not edit it manually.'))

    if interface in interface_uuids:
      uuid = interface_uuids[interface]
    elif __opts__['test']:
      uuid = 'will-generate-a-new-uuid'
    else:
      uuid = str(uuid4())

    kf.set_string('connection', 'id', interface)
    kf.set_string('connection', 'interface-name', interface)
    kf.set_string('connection', 'uuid', uuid)

    for section, options in dict(sorted(config.items())).items():
      if not isinstance(options, dict):
        log.error(f'Expected section, got "{section}={options}".')
        continue

      for option, value in dict(sorted(options.items())).items():
        if option in ['addresses', 'routes']:
          option = SINGULARS[option]

          i = 1

          for element in value:
            if isinstance(element, tuple):
              element = ','.join(element)

            kf.set_string(section, f'{option}{i}', element)

            i += 1

        elif isinstance(value, str):
          kf.set_string(section, option, value)

        elif isinstance(value, bool):
          kf.set_boolean(section, option, value)

        else:
          log.error(f'Unhandled data type "{option}={value}".')

    data[interface] = kf.to_data()[0]

  if data:
    states['network_nm_nmconnections'] = {
        'file.managed': [
          {
            'names': [
              {
                f'{settings["base"]}/{interface}.nmconnection': [
                  {'contents': content},
                ],
              } for interface, content in data.items()
            ],
          },
          {'mode': '0600'},
          {'user': 'root'},
          {'group': 'root'},
          {
            'require': [{'file': 'network_nm_nmconnection_backup'}] if interface_files else [],
          },
        ],
    }

    if settings['control'].get('apply', True):
      require = [
        {'file': 'network_nm_script'},
      ]

      if interface_files:
        require.append({'file': 'network_nm_nmconnection_backup'})

      states['network_nm_reload'] = {
          'cmd.run': [
            {
              'names': [
                {
                  f'{settings["script"]} reload {interface}': [
                    {'stateful': True},
                    {'onchanges': [{'file': f'{settings["base"]}/{interface}.nmconnection'}]},
                  ],
                } for interface in data
              ],
            },
            {
              'env': [
                {'SALTSAFE_TEST_MASTER': int(settings['control'].get('test_master', True))},
              ],
            },
            {
              'onchanges': [
                {'file': 'network_nm_nmconnections'},
              ],
            },
            {'require': require},
            {'shell': '/bin/sh'},
          ],
      }

  return states
