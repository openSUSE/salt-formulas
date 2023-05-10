{#-
Salt state file for managing virtual machine disks
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

{%- set mypillar = pillar.delegated_orchestra -%}
{%- set volume_prefix = 'lun_kvm_' -%}

{%- for disk, size in mypillar['disks'].items() %}
{%- if disk == 'root' %}
{%- set volume = volume_prefix ~ 'system' %}
{%- set netapp_vs = mypillar['netapp_vs_primary'] %}
{%- else %}
{%- set volume = volume_prefix ~ 'data' %}
{%- set netapp_vs = mypillar['netapp_vs_secondary'] %}
{%- endif %}
disk_{{ disk }}:
  vmdisk.present:
     - name: '{{ mypillar['deployhost'] }}_{{ disk }}'
     - host: '{{ mypillar['netapp_host'] }}'
     - size: '{{ size }}'
     - volume: '{{ volume }}'
     - cluster: '{{ mypillar['cluster'] }}'
     - vserver: '{{ netapp_vs }}'
     - igroup: '{{ mypillar['netapp_igroup_primary'] }}'
     - failhard: True
{%- endfor %}
