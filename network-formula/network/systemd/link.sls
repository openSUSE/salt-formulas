{#-
Salt state file for managing network devices using systemd
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
-#}

{%- set mypillar = salt['pillar.get']('network:systemd', {}) %}
{%- set directory = '/etc/systemd/network/' %}
{%- set files = [] %}

{%- set link = mypillar.get('link', {}) %}
{%- if link %}
network_systemd_link_config:
  file.managed:
    - names:
        {%- for name, config in link.items() %}
          {%- set file = '10-salt-' ~ name ~ '.link' %}
          {%- do files.append(file) %}
        - {{ directory }}{{ file }}:
            - contents:
                - {{ pillar.get('managed_by_salt_formula', '# Managed by the network formula') | yaml_encode }}
                {%- for section, settings in config.items() %}
                - '[{{ section }}]'
                  {%- for key, value in settings.items() %}
                - '{{ key }}={{ value }}'
                  {%- endfor %}
                {%- endfor %}
        {%- endfor %}
    - user: root
    - group: root
    - mode: '0644'
{%- endif %}

{%- if mypillar.get('clean', true) %}
  {%- for element in salt['file.find'](directory, type='f', print='name') %}
    {%- if element not in files %}
network_systemd_link_delete_{{ element }}:
  file.absent:
    - name: {{ directory }}{{ element }}
    {%- endif %}
  {%- endfor %}
{%- endif %}
