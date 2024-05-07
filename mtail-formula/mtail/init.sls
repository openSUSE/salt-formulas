{#-
Salt state file for managing mtail
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

{%- from 'mtail/map.jinja' import config %}

mtail_package:
  pkg.installed:
    - name: mtail 

{%- set sysconfig = [] %}
{%- for key, value in config['sysconfig']['args'].items() %}

{%- if value == true %}
{%- do sysconfig.append('-' ~ key) %}
{%- elif value == false %}
{%- do salt.log.debug('mtail: ignoring ' ~ key) %}
{%- elif value is string or value is number %}
{%- do sysconfig.append('-' ~ key ~ ' ' ~ value) %}
{%- else %}
{%- do salt.log.error('mtail: illegal sysconfig value') %}
{%- endif %}
{%- endfor %}

mtail_sysconfig:
  suse_sysconfig.sysconfig:
    - name: mtail
    - header_pillar: managed_by_salt_formula_sysconfig
    - key_values:
        ARGS: '{{ ' '.join(sysconfig) }}'
    - require:
      - pkg: mtail_package

{%- set programs = config.get('programs', []) %}
{%- if programs %}
{%- set programs_directory = config['sysconfig']['args']['progs'] %}
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
      - pkg: mtail_package

mtail_service:
  service.running:
    - name: mtail
    - enable: true
    - reload: true
    - require:
      - pkg: mtail_package
    - watch:
      - suse_sysconfig: mtail_sysconfig
      - file: mtail_programs

{%- else %}
mtail_service:
  service.dead:
    - name: mtail
    - enable: false
{%- endif %}
