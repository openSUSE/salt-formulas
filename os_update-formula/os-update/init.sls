{#-
Salt state file for managing os-update
Copyright (C) 2023-2024 Georg Pfuetzenreuter

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

{%- from './map.jinja' import options, config -%}

os-update_package:
  pkg.installed:
    - name: os-update

{%- if 'os-update' in pillar %}
os-update_config_file:
  file.managed:
    - name: /etc/os-update.conf
    - replace: false

os-update_config_values:
  file.keyvalue:
    - name: /etc/os-update.conf
    - key_values:
        {%- for option in options %}
        {%- if config[option] is string %}
        {%- set value = config[option] %}
        {%- else %}
        {%- set value = config[option] | join(' ') %}
        {%- endif %}
        {{ option | upper }}: '"{{ value }}"'
        {%- endfor %}
    {%- if opts['test'] %}
    - ignore_if_missing: true
    {%- endif %}
    - append_if_not_found: true
    - require:
      - pkg: os-update_package
      - file: os-update_config_file

os-update_config_header:
  file.prepend:
    - name: /etc/os-update.conf
    - text: {{ pillar.get('managed_by_salt_formula', '# Managed by the os_update formula') | yaml_encode }}

{%- elif grains.osfullname == 'openSUSE Tumbleweed' %}
os-update_config_file:
  file.absent:
    - name: /etc/os-update.conf
{%- endif %}

{%- if config.time or 'accuracysec' in config or 'randomizeddelaysec' in config %}
os-update_timer_unit:
  file.managed:
    - name: /etc/systemd/system/os-update.timer.d/override.conf
    - makedirs: True
    - contents:
        - {{ pillar.get('managed_by_salt_formula', '# Managed by the os_update formula') | yaml_encode }}
        - '[Timer]'
        {%- if config.time %}
        - 'OnCalendar='
        - 'OnCalendar={{ config.time }}'
        {%- endif %}
        {%- if 'accuracysec' in config %}
        - 'AccuracySec={{ config.accuracysec }}'
        {%- endif %}
        {%- if 'randomizeddelaysec' in config %}
        - 'RandomizedDelaySec={{ config.randomizeddelaysec }}'
        {%- endif %}
    - watch_in:
        - service: os-update_timer_service
{%- endif %}

os-update_timer_service:
  service.running:
    - name: os-update.timer
    - enable: {{ config.enable }}
    - require:
      - pkg: os-update_package
