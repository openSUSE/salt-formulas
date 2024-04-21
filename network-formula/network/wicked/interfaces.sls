{#-
Salt state file for managing network interfaces using Wicked
Copyright (C) 2023-2024 Georg Pfuetzenreuter <mail+opensuse@georg-pfuetzenreuter.net>

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
-#}

{%- from 'network/wicked/map.jinja' import base, base_backup, interfaces, script, do_apply -%}
{%- set ifcfg_data = {} %}
{%- set enslaved = [] %}
{%- set startmode_ifcfg = {'auto': [], 'off': []} %}

include:
  - .common

{%- for interface, config in interfaces.items() %}
{%- do ifcfg_data.update({ interface: {'addresses': [], 'startmode': 'auto'} }) %}

{%- if 'address' in config %}
{%- set addr = config['address'] %}
{%- elif 'addresses' in config %}
{%- set addr = config['addresses'] %}
{%- else %}
{%- set addr = None %}
{%- endif %}

{%- if addr is string %}
{%- do ifcfg_data[interface]['addresses'].append(addr) %}
{%- elif addr is iterable and addr is not mapping %}
{%- do ifcfg_data[interface]['addresses'].extend(addr) %}
{%- endif %}

{%- for option, value in config.items() %}
{%- if value is sameas true %}
{%- set value = 'yes' %}
{%- elif value is sameas false %}
{%- if option == 'startmode' %}
{%- set value = 'off' %}
{%- else %}
{%- set value = 'no' %}
{%- endif %}
{%- else %}
{%- set value = value | lower %}
{%- endif %}
{%- set option = option | lower %}
{%- if not option in ['address', 'addresses'] %}
{%- do ifcfg_data[interface].update({option: value}) %}
{%- endif %}
{%- endfor %}

{%- if ifcfg_data[interface]['startmode'] in startmode_ifcfg.keys() %}
{%- do startmode_ifcfg[ifcfg_data[interface]['startmode']].append(interface) %}
{%- endif %}

{%- if interface.startswith('br') and 'bridge_ports' in config %}
{%- if not 'bridge' in config %}
{%- do ifcfg_data[interface].update({'bridge': 'yes'}) %}
{%- endif %}
{%- do enslaved.extend(config['bridge_ports'].split()) %}
{%- endif %}

{%- endfor %}

{%- for interface, config in interfaces.items() %}
{%- if not 'bootproto' in config %}
{%- if interface in enslaved %}
{%- set bootproto = 'none' %}
{%- else %}
{%- set bootproto = 'static' %}
{%- endif %}
{%- do ifcfg_data[interface].update({'bootproto': bootproto}) %}
{%- endif %}

{%- endfor %}

{%- if ifcfg_data %}

{%- set interface_files = {} %}
{%- for interface in ifcfg_data.keys() %}
{%- set file = base ~ '/ifcfg-' ~ interface %}
{%- if salt['file.file_exists'](file) %}
{%- do interface_files.update({interface: file}) %}
{%- endif %}
{%- endfor %} {#- close interface loop #}

{%- if interface_files %}
network_wicked_ifcfg_backup:
  file.copy:
    - names:
      {%- for interface, file in interface_files.items() %}
      - {{ base_backup }}/ifcfg-{{ interface }}:
        - source: {{ file }}
      {%- endfor %}
    - require:
      - file: network_wicked_backup_directory
{%- endif %} {#- close interface_files check #}

network_wicked_ifcfg_settings:
  file.managed:
    - names:
      {%- for interface, config in ifcfg_data.items() %}
      - {{ base }}/ifcfg-{{ interface }}:
        - contents:
            - {{ pillar.get('managed_by_salt_formula', '# Managed by the network formula') | yaml_encode }}
          {%- for address in config.pop('addresses') %}
            - IPADDR_{{ loop.index }}='{{ address }}'
          {%- endfor %}
          {%- for key, value in config.items() %}
          {%- if value is string %}
            - {{ key | upper }}='{{ value }}'
          {%- else %}
          {%- do salt.log.warning('wicked: unsupported value for key ' ~ key) %}
          {%- endif %}
          {%- endfor %}
      {%- endfor %}
    - mode: '0640'
    {%- if interface_files %}
    - require:
      - file: network_wicked_ifcfg_backup
    {%- endif %}
{%- endif %}

{%- if do_apply and ( startmode_ifcfg['auto'] or startmode_ifcfg['off'] ) %}
network_wicked_interfaces:
  cmd.run:
    - names:
      {%- for interface in startmode_ifcfg['auto'] %}
      - {{ script }}up {{ interface }}:
        - stateful:
          - test_name: |
              if test -x {{ script }}up
              then
                {{ script }}up {{ interface }} test
              else
                echo 'changed=True comment="Helper script is not available" result=None'
              fi
        {%- if salt['cmd.retcode'](cmd='ifstatus ' ~ interface ~ ' -o quiet', ignore_retcode=True) == 0 %}
        - onchanges:
          - file: {{ base }}/ifcfg-{{ interface }}
        {%- endif %}
      {%- endfor %}
      {%- for interface in startmode_ifcfg['off'] %}
      - {{ script }}down {{ interface }}:
        - stateful:
          - test_name: {{ script }}down {{ interface }} test
        - onlyif: ifstatus {{ interface }} -o quiet
      {%- endfor %}
    - require:
      - file: network_wicked_script
      {%- if interface_files %}
      - file: network_wicked_ifcfg_backup
      {%- endif %}
      - file: network_wicked_ifcfg_settings
    - shell: /bin/sh
{%- endif %}
