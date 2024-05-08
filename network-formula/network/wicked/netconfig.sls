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

{%- if config %}
network_wicked_config:
  suse_sysconfig.sysconfig:
    - name: {{ base }}/config
    - header_pillar: managed_by_salt_formula_sysconfig
    - quote_integers: true
    - key_values:
      {%- for key, value in config.items() %}
        {%- if value is string %}
          {%- set value = value | lower %}
        {%- elif value is iterable %}
          {%- set value = ' '.join(value) | lower -%}
        {%- endif %}
        {{ key }}: {{ value }}
      {%- endfor %}

{%- if do_apply %}
network_wicked_netconfig_update:
  cmd.run:
    - name: netconfig update
    - onchanges:
      - suse_sysconfig: network_wicked_config
{%- endif %} {#- close do_apply check #}
{%- endif %}
