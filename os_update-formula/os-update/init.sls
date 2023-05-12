{#-
Salt state file for managing os-update
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

{%- from './map.jinja' import options, config -%}

os-update_package:
  pkg.installed:
    - name: os-update

os-update_config:
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
    - require:
      - pkg: os-update_package

{%- if config.time %}
os-update_timer_unit:
  file.managed:
    - name: /etc/systemd/system/os-update.timer.d/override.conf
    - makedirs: True
    - contents: |
        [Timer]
        OnCalendar=
        OnCalendar={{ config.time }}
{%- endif %}

os-update_timer_service:
  service.running:
    - name: os-update.timer
    - enable: {{ config.enable }}
    - require:
      - pkg: os-update_package
    {%- if config.time %}
    - watch:
      - file: os-update_timer_unit
    {%- endif %}
