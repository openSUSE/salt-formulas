{#-
Salt state file for removing unmanaged httpd configuration files
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

{%- from 'apache_httpd/map.jinja' import httpd, places, cmd_kwargs -%}

include:
  - .services

{%- for place in places %}
  {%- set directory = httpd.directories[place] %}
  {%- for file in salt['file.find'](directory, print='name', type='f') %}
    {%- set path = directory ~ '/' ~ file %}
    {%- do salt.log.debug('apache_httpd.purge: ' ~ path) %}
    {#- RPM file query is not implemented in modules.rpm_lowpkg #}
    {%- if
          salt['cmd.retcode']('/usr/bin/rpm -fq --quiet ' ~ path, **cmd_kwargs) == 1
          and
          file.replace('.conf', '') not in httpd.get(place, {})
    %}
apache_httpd_remove_{{ place }}-{{ file }}:
  file.absent:
    - name: {{ path }}
    - watch_in:
        - service: apache_httpd_service
    {%- endif %}
  {%- endfor %}
{%- endfor %}
