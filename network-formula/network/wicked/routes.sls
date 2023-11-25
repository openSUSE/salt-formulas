{#-
Salt state file for managing network routes using Wicked
Copyright (C) 2023 Georg Pfuetzenreuter <mail+opensuse@georg-pfuetzenreuter.net>

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

{%- from 'network/wicked/map.jinja' import base, base_backup, routes, script, do_apply -%}

include:
  - .common
  - .service

{%- set file = base ~ '/routes' %}
{%- if salt['file.file_exists'](file) %}
{%- set backup = True %}
network_wicked_routes_backup:
  file.copy:
    - names:
      - {{ base_backup }}/routes:
        - source: {{ file }}
{%- else %}
{%- set backup = False %}
{%- endif %}

{%- if routes %}
{%- set shell_routes = [] %}

network_wicked_routes:
  file.managed:
    - name: {{ file }}
    - contents:
        - {{ pillar.get('managed_by_salt_formula', '# Managed by the network formula') | yaml_encode }}
      {%- for route, config in routes.items() %}
      {%- if route in ['default4', 'default6'] %}
      {%- set route = 'default' %}
      {%- endif %}
      {%- do shell_routes.append(route ~ '_' ~ config.get('gateway', '')) %}
      {%- set options = config.get('options', []) %}
        - '{{ route }} {{ config.get('gateway', '-') }} {{ config.get('netmask', '-') }} {{ config.get('interface', '-') }}{{ ' ' ~ ' '.join(options) if options else '' }}'
      {%- endfor %}
    - mode: '0640'

{%- if do_apply %}
network_wicked_routes_reload:
  cmd.run:
    - name: {{ script }}routes
    {%- if salt['file.file_exists'](script ~ 'routes') %}
    - stateful:
      - test_name: {{ script }}routes '{{ ','.join(shell_routes) }}' test
    {%- else %}
    - stateful: true
    {%- endif %}
    - require:
      - file: network_wicked_script
      - file: network_wicked_script_links
      {%- if backup %}
      - file: network_wicked_routes_backup
      {%- endif %}
    - onchanges:
      - file: network_wicked_routes
{%- endif %} {#- close do_apply check #}
{%- endif %}
