{#-
Salt state file for managing Redis
Copyright (C) 2023 SUSE LLC <georg.pfuetzenreuter@suse.com>

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

{%- from 'redis/map.jinja' import config, dirs, package -%}

redis_package:
  pkg.installed:
    - name: {{ package }}

{%- for instance, settings in config.items() %}

redis_{{ instance }}_config:
  file.managed:
    - name: {{ dirs['config'] }}/{{ instance }}.conf
    - contents:
      {%- for key, value in settings.items() %}
      {%- if value is string and '%%INSTANCE%%' in value %}
      {%- set value = value.replace('%%INSTANCE%%', instance) %}
      {%- endif %}
      - {{ key }} {{ value }}
      {%- endfor %}
    - user: root
    - group: redis
    - mode: '0640'
    - require:
      - pkg: redis_package

redis_{{ instance }}_directory:
  file.directory:
    - name: {{ dirs['data'] }}/{{ instance }}
    - user: redis
    - group: redis
    - mode: '0750'
    - require:
      - pkg: redis_package

redis_{{ instance }}_service:
  service.running:
    - name: redis@{{ instance }}
    - enable: True
    - watch:
      - file: redis_{{ instance }}_config

{%- endfor %}
