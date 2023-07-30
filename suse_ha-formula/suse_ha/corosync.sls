{#-
Salt state file for managing Corosync
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

{%- from 'suse_ha/map.jinja' import hapillar, cluster, fencing, multicast, is_primary -%}
{%- if 'sbd' in fencing -%}{%- set hook_sbd = True -%}{%- else -%}{%- set hook_sbd = False %}{%- endif %}

include:
  - .packages
  {%- if hook_sbd %}
  - .sbd
  {%- endif %}

{%- if 'name' in cluster %}
corosync.service:
  service.running:
    - enable: False
    - reload: False
    - require:
      - suse_ha_packages
      {%- if hook_sbd %}
      - service: sbd_service
      {%- endif %}
    - watch:
      - file: /etc/corosync/corosync.conf
      - file: /etc/corosync/authkey
      {%- if hook_sbd %}
      {%- if is_primary %}
      - cmd: sbd_format_devices
      {%- endif %}
      - file: sbd_sysconfig
      {%- endif %}

/etc/corosync/authkey:
  file.managed:
    - name: /etc/corosync/authkey
    {%- if 'cluster_secret' in hapillar %}
    - contents_pillar: 'suse_ha:cluster_secret'
    {%- else %}
    - contents: 'fix-me-please'
    {%- do salt.log.error('suse_ha: No cluster secret provided - Corosync will not operate!') %}
    {%- endif %}
    - user: root
    - group: root
    - mode: '0400'

/etc/corosync/corosync.conf:
  file.managed:
    - source:  salt://{{ slspath }}/files/etc/corosync/corosync.conf
    - template: jinja
    - user: root
    - group: root
    - mode: '0644'
    - context:
        cluster: {{ cluster }}
        multicast: {{ multicast }}
    - require:
      - suse_ha_packages
{%- else %}
{%- do salt.log.error('suse_ha: cluster pillar not configured, not sending any Corosync configuration!') %}
{%- endif %}
