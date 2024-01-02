{#-
Salt state file for managing libvirt-guests
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

{%- from 'libvirt/map.jinja' import config -%}

{%- set options = config.get('guests', {}) %}

{%- if 'enable' in options %}
{%- set enable = options.pop('enable') %}
{%- else %}
{%- set enable = True %}
{%- endif %}

{%- if options %}
libvirt_guests_sysconfig_file:
  file.managed:
    - name: /etc/sysconfig/libvirt-guests
    - replace: false

libvirt_guests_sysconfig:
  file.keyvalue:
    - name: /etc/sysconfig/libvirt-guests
    - key_values:
        {%- for key, value in options.items() %}
        {{ key | upper }}: {{ value }}
        {%- endfor %}
    - append_if_not_found: true
    - ignore_if_missing: {{ opts['test'] }}
    - require:
      - file: libvirt_guests_sysconfig_file
{%- endif %}

libvirt_guests_service:
{%- if enable %}
  service.running:
    - name: libvirt-guests
    - enable: true
    {%- if options %}
    - require:
      - file: libvirt_guests_sysconfig
    {%- endif %}
{%- else %}
  service.dead:
    - name: libvirt-guests
    - enable: false
{%- endif %}
