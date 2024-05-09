{#-
Salt state file for managing generic bootloader configuration
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

{%- from 'bootloader/map.jinja' import bootloader_data -%}

{%- if 'config' in bootloader_data %}
bootloader_sysconfig:
  suse_sysconfig.sysconfig:
    - name: bootloader
    - header_pillar: managed_by_salt_formula_sysconfig
    - append_if_not_found: True
    - quote_booleans: False
    - key_values: {{ bootloader_data['config'] }}

{%- if bootloader_data.get('update', True) %}
bootloader_update:
  cmd.run:
    {#- on 15.4 pbl is not yet available under /usr #}
    - name: /sbin/pbl --install
    - onchanges:
      - suse_sysconfig: bootloader_sysconfig
{%- endif %}
{%- endif %}
