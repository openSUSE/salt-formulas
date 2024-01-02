{#-
Salt state file for managing SUSE HA related init/systemd services
Copyright (C) 2023-2024 SUSE LLC <georg.pfuetzenreuter@suse.com>

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

{%- from 'suse_ha/map.jinja' import cluster -%}

{%- if 'name' in cluster %}
pacemaker.service:
  service.running:
    - enable: True
    - reload: True
    - require:
      - suse_ha_packages
      - corosync.service
    - watch:
      - file: /etc/sysconfig/pacemaker
{%- else %}
{%- do salt.log.error('suse_ha: cluster pillar not configured, not enabling Pacemaker!') %}
{%- endif %}
