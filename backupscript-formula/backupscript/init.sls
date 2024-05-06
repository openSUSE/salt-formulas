{#-
Salt state file for managing SUSE backup scripts
Copyright (C) 2024 Georg Pfuetzenreuter <mail+opensuse@georg-pfuetzenreuter.net>

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

{%- set mypillar = pillar.get('backupscript', {}) %}

{%- set backupscripts = {
      'influxdb': mypillar.get('influxdb', False),
      'mysql': mypillar.get('mysql', False),
      'postgresql': mypillar.get('postgresql', False),
    }
-%}

{%- if backupscripts['influxdb'] != False or backupscripts['mysql'] != False or backupscripts['postgresql'] != False %}

backupscript_packages:
  pkg.installed:
    - pkgs:
        {%- for bs_short in backupscripts.keys() %}
        {%- if backupscripts[bs_short] != False %}
        - {{ bs_short }}-backupscript
        {%- endif %}
        {%- endfor %}

{%- for bs_short, config in backupscripts.items() %}
{%- set bs = bs_short ~ '-backupscript' %}

{%- if config %}
{%- set file = '/etc/sysconfig/' ~ bs %}

{{ bs }}_sysconfig_header:
  suse_sysconfig.header:
    - name: {{ file }}
    - header_pillar: managed_by_salt_formula_sysconfig
    - require:
        - pkg: backupscript_packages

{{ bs }}_sysconfig:
  file.keyvalue:
    - name: {{ file }}
    - key_values:
      {%- for k, v in config.items() %}
      {%- if v is string %}
      {%- set v = '"' ~ v ~ '"' %}
      {%- elif v is sameas true %}
      {%- set v = '"yes"' %}
      {%- elif v is sameas false %}
      {%- set v = '"no"' %}
      {%- endif %}
        {{ k | upper }}: '{{ v }}'
      {%- endfor %}
    - ignore_if_missing: {{ opts['test'] }}
    - require:
        - pkg: backupscript_packages

{%- endif %}  {#- close config check #}

{%- if backupscripts[bs_short] != False %}
{{ bs }}_timer:
  service.running:
    - name: {{ bs }}.timer
    - enable: true
    - require:
        - pkg: backupscript_packages
        {%- if config %}
        - file: {{ bs }}_sysconfig
        {%- endif %}
{%- endif %}

{%- endfor %} {#- close backupscripts loop #}
{%- endif %}  {#- close backupscripts not false check #}

{%- for bs in backupscripts.keys() %}
{%- if backupscripts[bs] == False %}
{%- set bs = bs ~ '-backupscript' %}
{%- if salt['service.available'](bs) %}
{{ bs }}_service:
  service.dead:
    - names:
        {%- if not opts['test'] %}
        {#- not idempotent in test mode #}
        - {{ bs }}.service
        {%- endif %}
        - {{ bs }}.timer
    - enable: false
{%- endif %}  {#- close backupscript service check #}
{%- endif %}  {#- close backupscript false check #}
{%- endfor %} {#- close backupscripts loop #}
