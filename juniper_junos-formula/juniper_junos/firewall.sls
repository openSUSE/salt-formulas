{#-
Salt state file for managing Juniper Junos based network firewalls
Copyright (C) 2023 SUSE LLC

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

{%- from 'juniper_junos/map.jinja' import config, options -%}

junos_firewall:
  netconfig.managed:
    - template_name: salt://{{ slspath }}/files/firewall.j2
    - debug: true
    - present_ifaces: {{ salt['susejunos.get_active_interfaces'](include_xe=false) }}
    {%- for option in options['firewall'] %}
    - {{ option }}: {{ config.get(option, []) }}
    {%- endfor %}
