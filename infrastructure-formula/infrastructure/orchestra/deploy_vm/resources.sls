{#-
Salt orchestration state file for managing virtual machine resources
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

{%- from slspath ~ '/map.jinja' import lockfile, clusterprimary, fqdn, lowpillar, domain, cluster, fqdn -%}

check_lock:
  lock.check:
    - name: '{{ lockfile }}'
    - failhard: True

lock:
  lock.lock:
    - name: '{{ lockfile }}'
    - failhard: True

hypervisor_vm_resources:
  salt.state:
    - tgt: '{{ clusterprimary }}'
    - sls:
      - infrastructure.libvirt.domains
      - infrastructure.suse_ha.resources
    - pillar:
        do_vd: True
        delegated_orchestra:
          lowpillar: {{ lowpillar }}
          domain: {{ domain }}
          cluster: {{ cluster }}
          deployhost: {{ fqdn }}
    - saltenv: {{ saltenv }}
    - pillarenv: {{ saltenv }}

hypervisor_vm_start:
  salt.function:
    - name: cmd.run
    - tgt: '{{ clusterprimary }}'
    - arg:
      - 'crm resource status VM_{{ fqdn }} 2> >(grep -q "NOT running") && crm resource start VM_{{ fqdn }}'
    - kwarg:
        shell: /usr/bin/bash
    - require:
        - hypervisor_vm_resources

unlock:
  lock.unlock:
    - name: '{{ lockfile }}'
