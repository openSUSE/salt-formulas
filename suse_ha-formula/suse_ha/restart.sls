{#-
Salt state file for managing SUSE HA cluster restarts
Copyright (C) 2024 SUSE LLC <georg.pfuetzenreuter@suse.com>

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

{%- from 'suse_ha/map.jinja' import is_standby -%}
{%- set file = '/var/adm/suse_ha_pending_restart' %}

{%- if salt ['file.file_exists'](file) or is_standby %}
  {%- if is_standby %}

suse_ha_restart:
  cmd.run:
    - name: /usr/sbin/crm cluster restart
    - shell: /bin/sh
    - timeout: 600

suse_ha_clear_pending_restart:
  file.absent:
    - name: {{ file }}
    - require:
        - cmd: suse_ha_restart

  {%- else %}
    {%- do salt.log.warning('suse_ha: restart from previous execution is still pending, node is not in standby mode!')
  {%- endif %} {#- close inner standby check #}

{%- else %}

suse_ha_restart:
  # file.managed would be more appropriate, but the file module does not offer a mod_watch function and we would need additional logic to differentiate between cmd and file in the calling watch directives
  cmd.run:
    - name: touch {{ file }}
    - creates: {{ file }}
    - shell: /bin/sh

{%- endif %} {#- close file or standby check #}
