{#-
Salt state file for managing the general network configuration
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

{%- from 'network/wicked/map.jinja' import base, config, do_apply -%}

network_wicked_config_header:
  suse_sysconfig.header:
    - name: {{ base }}/config
    - fillup: config-wicked
    - header_pillar: managed_by_salt_formula_sysconfig

{%- if config %}
network_wicked_config:
  file.keyvalue:
    - name: {{ base }}/config
    - key_values:
      {%- for key, value in config.items() %}
      {%- if value is sameas true %}
      {%- set value = 'yes' %}
      {%- elif value is sameas false %}
      {%- set value = 'no' %}
      {%- elif value is iterable and value is not string %}
      {%- set value = ' '.join(value) | lower -%}
      {%- else %}
      {%- set value = value | lower %}
      {%- endif %}
        {{ key | upper }}: '"{{ value }}"'
      {%- endfor %}
    - ignore_if_missing: {{ opts['test'] }}
    - require:
      - file: network_wicked_config_header

{%- if do_apply %}
network_wicked_netconfig_update:
  cmd.run:
    - name: netconfig update
    - onchanges:
      - file: network_wicked_config
{%- endif %} {#- close do_apply check #}
{%- endif %}
