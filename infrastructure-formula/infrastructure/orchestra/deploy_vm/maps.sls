{#-
Salt orchestration state file for managing LUN/multipath mapping files
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

{%- from slspath ~ '/map.jinja' import lockfile, cluster, ansiblegate, clusterprimary, netapp_host, fqdn, disks -%}

check_lock:
  lock.check:
    - name: '{{ lockfile }}'
    - failhard: True

lock:
  lock.lock:
    - name: '{{ lockfile }}'
    - failhard: True

hypervisor_lunmap:
  salt.state:
    - tgt: '{{ cluster }}*'
    - sls:
      - lunmap

hypervisor_mpathmap:
  salt.state:
    - tgt: {{ ansiblegate }}
    - sls:
      - orchestra.mpathmap
    - pillar:
        delegated_orchestra:
          clusterprimary: {{ clusterprimary }}
          netapphost: {{ netapp_host }}
          deployhost: {{ fqdn }}
          disks: {{ disks }}
    - saltenv: {{ saltenv }}
    - pillarenv: {{ saltenv }}

unlock:
  lock.unlock:
    - name: '{{ lockfile }}'
