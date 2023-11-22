{#-
Salt state file for managing rebootmgr
Copyright (C) 2023 Georg Pfuetzenreuter

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

{%- from './map.jinja' import options, config, os -%}

rebootmgr_package:
  pkg.installed:
    - name: rebootmgr

{%- if 'rebootmgr' in pillar %}
{%- if os == 'openSUSE Tumbleweed' %}
rebootmgr_config_file:
  file.managed:
    - name: /etc/rebootmgr.conf
    - replace: false
{%- endif %}

rebootmgr_config:
  file.keyvalue:
    - name: /etc/rebootmgr.conf
    - key_values:
        {%- for option in options %}
        {{ option }}: '"{{ config[option] }}"'
        {%- endfor %}
    - ignore_if_missing: {{ opts['test'] }}
    {%- if os == 'openSUSE Tumbleweed' %}
    - append_if_not_found: true
    {%- endif %}
    - require:
      {%- if os == 'openSUSE Tumbleweed' %}
      - file: rebootmgr_config_file
      {%- else %}
      - pkg: rebootmgr_package
      {%- endif %}

{%- elif os == 'openSUSE Tumbleweed' %}
rebootmgr_config_file:
  file.absent:
    - name: /etc/rebootmgr.conf
{%- endif %}

rebootmgr_service:
  service.running:
    - name: rebootmgr
    - enable: {{ config.get('enable', True) }}
    {%- if 'rebootmgr' in pillar %}
    - watch:
      - file: rebootmgr_config
    {%- endif %}
    - require:
      - pkg: rebootmgr_package
