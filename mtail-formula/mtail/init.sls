{#-
Salt state file for managing mtail
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

{%- from 'mtail/map.jinja' import config %}

mtail_package:
  pkg.installed:
    - name: mtail 

{%- set sysconfig = [] %}
{%- for key, value in config['sysconfig']['args'].items() %}
{%- if value is string %}
{%- do sysconfig.append('-' ~ key ~ ' ' ~ value) %}
{%- elif value is sameas true %}
{%- do sysconfig.append('-' ~ key) %} %}
{%- elif value is not sameas false %}
{%- do salt.log.error('mtail: illegal sysconfig value') %}
{%- endif %}
{%- endfor %}

mtail_sysconfig:
  file.keyvalue:
    - name: /etc/sysconfig/mtail
    - key: ARGS
    - value: '"{{ ' '.join(sysconfig) }}"'
    - require:
      - pkg: mtail_package

{%- set programs_directory = config['sysconfig']['args']['progs'] %}
mtail_programs_directory:
  file.directory: {#- TODO: submit directory installation to the package #}
    - name: {{ programs_directory }}
    - group: mtail
    - require:
      - pkg: mtail_package

{%- set programs = config.get('programs', []) %}
{%- if programs %}
mtail_programs:
  file.managed:
    - names:
      {%- for program in programs %}
      {%- set program_file = program ~ '.mtail' %}
      - {{ programs_directory }}/{{ program_file }}:
        {#- prefer custom programs, default to formula provided ones #}
        - source: salt://files/mtail/programs/{{ program_file }}
        - source: salt://mtail/programs/{{ program_file }}
      {%- endfor %}
    - require:
      - file: mtail_programs_directory

{#- TODO: repair packaged service to correctly implement "reload" #}
mtail_reload:
  cmd.run:
    - name: systemctl is-active mtail && systemctl kill --signal=SIGHUP mtail || true
    - onchanges:
      - file: mtail_programs
    - require:
      - pkg: mtail_package

mtail_service:
  service.running:
    - name: mtail
    - enable: true
    - reload: false
    - require:
      - pkg: mtail_package
      - file: mtail_programs

{%- else %}
mtail_service:
  service.dead:
    - name: mtail
    - enable: false
{%- endif %}
