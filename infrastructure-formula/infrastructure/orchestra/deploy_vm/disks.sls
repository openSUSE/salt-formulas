{#-
Salt orchestration state file for managing virtual machine disks
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

{%- from slspath ~ '/map.jinja' import lockfile, ansiblegate, fqdn, disks, netapp_host, netapp_igroup_primary, netapp_vs_primary, netapp_vs_secondary, cluster -%}

check_lock:
  lock.check:
    - name: '{{ lockfile }}'
    - failhard: True

lock:
  lock.lock:
    - name: '{{ lockfile }}'
    - failhard: True

vm_disks:
  salt.state:
    - tgt: {{ ansiblegate }}
    - sls:
      - orchestra.vmdisks
    - pillar:
        delegated_orchestra:
          deployhost: {{ fqdn }}
          disks: {{ disks }}
          netapp_host: {{ netapp_host }}
          netapp_igroup_primary: {{ netapp_igroup_primary }}
          netapp_vs_primary: {{ netapp_vs_primary }}
          netapp_vs_secondary: {{ netapp_vs_secondary }}
          cluster: {{ cluster }}
    - saltenv: {{ saltenv }}
    - pillarenv: {{ saltenv }}

unlock:
  lock.unlock:
    - name: '{{ lockfile }}'
