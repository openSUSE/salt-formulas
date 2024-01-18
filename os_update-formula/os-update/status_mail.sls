{#-
Salt state file for managing systemd-status-mail
Copyright (C) 2024 Georg Pfuetzenreuter

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

{%- from './map.jinja' import config_sm -%}
{%- set file = '/etc/default/systemd-status-mail' %}
{%- set services = config_sm.get('services', []) %}

status-mail_package:
  pkg.installed:
    - name: systemd-status-mail

{%- if config_sm %}
{%- if 'config' in config_sm %}
status-mail_config_file:
  file.managed:
    - name: {{ file }}
    - replace: false

status-mail_config_values:
  file.keyvalue:
    - name: {{ file }}
    - key_values:
        {%- for key, value in config_sm['config'].items() %}
        {{ key | upper }}: '"{{ value }}"'
        {%- endfor %}
    {%- if opts['test'] %}
    - ignore_if_missing: true
    {%- endif %}
    - append_if_not_found: true
    - require:
      - pkg: status-mail_package
      - file: status-mail_config_file

status-mail_config_header:
  file.prepend:
    - name: {{ file }}
    - text: {{ pillar.get('managed_by_salt_formula', '# Managed by the os_update formula') | yaml_encode }}
    - require:
      - pkg: status-mail_package

{%- endif %} {#- close config in pillar check #}

{%- if services and services is not string and services is not mapping %}
status-mail_services:
  file.managed:
    - names:
        {%- for service in services %}
        - /etc/systemd/system/{{ service }}.service.d/status-mail.conf
        {%- endfor %}
    - makedirs: True
    - contents:
        - {{ pillar.get('managed_by_salt_formula', '# Managed by the os_update formula') | yaml_encode }}
        - '[Unit]'
        - 'OnFailure=systemd-status-mail@%n.service'
    - require:
      - pkg: status-mail_package
{%- endif %}
{%- endif %} {#- close status-mail pillar check #}


{%- for found_file in salt['file.find']('/etc/systemd/system', name='status-mail.conf', type='f') %}
{%- set service = found_file.replace('/etc/systemd/system/', '').replace('.service.d/status-mail.conf', '') %}
{%- if service not in services %}
status-mail_disable_{{ service }}:
  file.absent:
    - name: {{ found_file }}
{%- endif %}
{%- endfor %}
{#- might leave empty service.d directories behind, but better than accidentally deleting other override files #} 


{%- if not config_sm or not 'config' in config_sm %}
status-mail_config_file:
  file.absent:
    - name: {{ file }}
{%- endif %}
