{#-
Salt state file for managing smartd
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

{%- from 'smartmontools/map.jinja' import smartd %}
{%- set config = smartd.get('config', []) %}

include:
  - .

smartmontools_smartd_config:
  file.managed:
    - name: /etc/smartd.conf
    - template: jinja
    - contents:
        - {{ pillar.get('managed_by_salt_formula', '# Managed by the smartmontools formula') | yaml_encode }}
        {%- for entry in config %}
        - {{ entry }}
        {%- endfor %}

smartmontools_smartd_service:
  service.running:
    - name: smartd
    {#- service is already enabled through a vendor preset on SUSE distributions, but doesn't hurt to enforce it #}
    - enable: true
    - require:
        - pkg: smartmontools_package
    - watch:
        - file: smartmontools_smartd_config
