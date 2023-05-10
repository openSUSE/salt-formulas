{#-
Salt state file for managing libvirt domains
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

{%- set myid = grains['id'] -%}
{%- if pillar['do_vd'] | default(False) and 'delegated_orchestra' in pillar -%}
{%- do salt.log.debug('libvirt.domains: delegated from orchestration run') -%}
{%- set dopillar = pillar['delegated_orchestra'] -%}
{%- set lowpillar = dopillar['lowpillar'] -%}
{%- set domain = dopillar['domain'] -%}
{%- set cluster = dopillar['cluster'] -%}
{%- else -%}
{%- do salt.log.debug('libvirt.domains: running non-orchestrated') -%}
{%- set domain = grains['domain'] -%}
{%- set cluster = grains['virt_cluster'] -%}
{%- set lowpillar = salt['pillar.get']('infrastructure') -%}
{%- endif -%} {#- close do_vd check -#}
{%- if not 'domains' in lowpillar -%}
{%- do salt.log.error('Incomplete orchestration pillar - verify whether the orchestrator role is assigned.') -%}
{%- elif not domain in lowpillar['domains'] -%}
{%- do salt.log.error('Domain ' ~ domain ~ ' not correctly registered in pillar/domain or orchestrator role is not assigned!') -%}
{%- else -%}
{%- set domainpillar = lowpillar['domains'][domain] -%}
{%- set clusterpillar = domainpillar['clusters'] -%}
{%- set machinepillar = domainpillar['machines'] -%}
{%- set basepath = '/kvm/vm/' -%}

{%- if not salt['file.file_exists']('/etc/uuidmap') %}
/etc/uuidmap:
  file.touch
{%- endif %}

{%- if cluster in clusterpillar and myid == clusterpillar[cluster]['primary'] %}
{%- if machinepillar is not none %}
{%- for machine, config in machinepillar.items() %}
{%- set machine = machine ~ '.' ~ domain %}
{%- if config['cluster'] == cluster %}
write_domainfile_{{ machine }}:
  file.managed:
    - template: jinja
    - names:
      - {{ basepath }}{{ machine }}.xml:
        - source: salt://files/libvirt/domains/{{ cluster }}.xml.j2
        - context:
            vm_name: {{ machine }}
            vm_memory: {{ config['ram'] }}
            vm_cores: {{ config['vcpu'] }}
            vm_disks: {{ config['disks'] }}
            vm_interfaces: {{ config['interfaces'] }}

vm_uuid_map_{{ machine }}:
  file.append:
  - name: /etc/uuidmap
  - text: '{{ machine }}: {{ salt['cmd.run']('uuidgen') }}'
  - unless: 'grep -q {{ machine }} /etc/uuidmap'
{%- endif %}
{%- endfor %}
{%- endif %}

{%- else %}

{%- do salt.log.warning('Libvirt: Skipping domain XML management due to non-primary minion ' ~ myid ~ ' in cluster ' ~ cluster) %}

{%- endif %}

{#- close domain pillar check -#}
{%- endif %}
