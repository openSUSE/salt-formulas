{#-
Salt state file for managing virtual machine resources in a SUSE HA cluster
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

{%- from 'suse_ha/macros.jinja' import primitive_resource -%}

{#- virtual machine resources below are constructed if instructed by the deploy_vm orchestration state #}
{%- if pillar['do_vd'] | default(False) %}
{%- if 'delegated_orchestra' in pillar %}
{%- set dopillar = pillar['delegated_orchestra'] -%}
{%- set lowpillar = dopillar['lowpillar'] -%}
{%- set domain = dopillar['domain'] -%}
{%- else %}
{%- set lowpillar = salt['pillar.get']('infrastructure') -%}
{%- set domain = grains['domain'] -%}
{%- endif %}
{%- set myid = grains['id'] -%}
{%- set cluster = grains['virt_cluster'] -%}
{%- if not 'domains' in lowpillar -%}
{%- do salt.log.error('Incomplete orchestration pillar - verify whether the orchestrator role is assigned.') -%}
{%- elif not domain in lowpillar['domains'] -%}
{%- do salt.log.error('Domain ' ~ domain ~ ' not correctly registered in pillar/domain or orchestrator role is not assigned!') -%}
{%- else -%}
{%- set domainpillar = lowpillar['domains'][domain] -%}
{%- set clusterpillar = domainpillar['clusters'] -%}
{%- set machinepillar = domainpillar['machines'] -%}

{%- if cluster in clusterpillar and myid == clusterpillar[cluster]['primary'] %}
{%- if machinepillar is not none %}
{%- for machine, config in machinepillar.items() %}
{%- set machine = machine ~ '.' ~ domain %}
{%- do salt.log.debug(machine) %}
{%- if config['cluster'] == cluster %}

{%- set instance_attributes = {
      'config': '/kvm/vm/' ~ machine ~ '.xml',
      'hypervisor': 'qemu:///system',
      'autoset_utilization_cpu': 'true',
      'autoset_utilization_hv_memory': 'true',
      'migration_transport': 'tcp',
      'migrateport': 16509
} %}

{%- set operations = {
      'monitor': {'timeout': 30, 'interval': 10},
      'start': {'timeout': 90, 'interval': 0},
      'stop': {'timeout': 90, 'interval': 0},
      'migrate_to': {'timeout': 600, 'interval': 0},
      'migrate_from': {'timeout': 550, 'interval': 0}
} %}

{%- set meta_attributes = {
      'target-role': 'Started',
      'priority': 0,
      'migration-threshold': 0
} %}

{{ primitive_resource('VM_' ~ machine, 'ocf', 'VirtualDomain', instance_attributes, operations, meta_attributes, 'heartbeat') }}

{%- endif %}
{%- endfor %}
{%- endif %}
{%- endif %}
{%- endif %}
{%- else %}
{%- do salt.log.debug('Skipping construction of Virtual Domain resources') %}
{%- endif %}
