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
{%- set cluster = grains['virt_cluster'].replace('-bare','') -%}
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
{%- set topdir = lowpillar.get('kvm_topdir', '/kvm') -%}
{%- set domaindir = lowpillar.get('libvirt_domaindir', topdir ~ '/vm') -%}

{%- if not salt['file.file_exists']('/etc/uuidmap') %}
/etc/uuidmap:
  file.touch
{%- endif %}

{%- if cluster in clusterpillar and myid == clusterpillar[cluster]['primary'] %}
{%- if machinepillar is not none %}
{%- for machine, config in machinepillar.items() %}
{%- set machine = machine ~ '.' ~ domain %}
{%- if config['cluster'] == cluster %}
{%- set domainxml = domaindir ~ '/' ~ machine ~ '.xml' %}
{%- if salt['cmd.retcode']('grep -q uuid ' ~ domainxml) == 0 %}
{%- set uuid = salt['cmd.run']('grep -oP "(?<=<uuid>).*(?=</uuid>)" ' ~ domainxml) %}
{%- do salt.log.debug('infrastructure.libvirt: found existing uuid') %}
{%- else %}
{%- set uuid = salt['cmd.run']('uuidgen') %}
{%- do salt.log.debug('infrastructure.libvirt: generated new uuid') %}
{%- endif %}
{%- do salt.log.debug('infrastructure.libvirt: uuid set to ' ~ uuid) %}
write_domainfile_{{ machine }}:
  file.managed:
    - template: jinja
    - names:
      - {{ domainxml }}:
        - source: salt://files/libvirt/domains/{{ cluster }}.xml.j2
        - context:
            vm_uuid: {{ uuid }}
            vm_name: {{ machine }}
            vm_memory: {{ config['ram'] }}
            vm_cores: {{ config['vcpu'] }}
            vm_disks: {{ config['disks'] }}
            vm_interfaces: {{ config['interfaces'] }}

vm_uuid_map_{{ machine }}:
  file.append:
  - name: /etc/uuidmap
  - text: '{{ machine }}: {{ uuid }}'
  - unless: 'grep -q {{ machine }} /etc/uuidmap'

{%- if clusterpillar[cluster].get('storage') == 'local' and 'image' in config %}
define_domain_{{ machine }}:
  module.run: {#- virt state does not support defining domains from custom XML files #}
    - virt.define_xml_path:
        - path: {{ domainxml }}
    - onchanges:
      - file: write_domainfile_{{ machine }}

{%- if 'root' in config['disks'] %}
{%- set root_disk = topdir ~ '/disks/' ~ machine ~ '_root.qcow2' %}
{%- set image = topdir ~ '/os-images/' ~ config['image'] %}
{%- set reinit = config.get('irreversibly_wipe_and_overwrite_vm_disk', False) %}

write_vmdisk_{{ machine }}_root:
  file.copy:
    - name: {{ root_disk }}
    - source: {{ image }}
    {%- if reinit is sameas true %}
    - force: true
    {%- endif %}

{%- set disk_size = config['disks']['root'] %}
{%- set image_info = salt['cmd.run']('qemu-img info --out json ' ~ image) | load_json %}
{%- set image_size = image_info['virtual-size'] %}

{%- if disk_size.endswith('G') %}
{%- set converted_size = ( disk_size.rstrip('G') | int * 1073741824 ) | int %}
{%- else %}
{%- do salt.log.error('infrastructure.libvirt: sizes need to end with "G", illegal disk size ' ~ disk_size ~ ' for machine ' ~ machine) %}
{%- set converted_size = None %}
{%- endif %} {#- close suffix check #}

{%- if converted_size %}
{%- do salt.log.debug('infrastructure.libvirt: converted size is ' ~ converted_size) %}

{%- if converted_size > image_size %}
{%- set disk_info = salt['cmd.run']('qemu-img info --out json -U ' ~ root_disk) | load_json %}
{%- set current_size = disk_info['virtual-size'] %}
{%- do salt.log.debug('infrastructure.libvirt: current disk size is ' ~ current_size) %}

{%- if current_size < converted_size %}
resize_vmdisk_{{ machine }}_root:
  cmd.run:
    - name: |
      {%- if machine in salt['virt.list_active_vms']() %}
        virsh blockresize {{ machine }} {{ root_disk }} {{ disk_size }}
      {%- else %}
        qemu-img resize {{ root_disk }} {{ disk_size }}
      {%- endif %}
    - require:
      - file: write_vmdisk_{{ machine }}_root
{%- endif %} {#- close current/converted size comparison check #}
{%- endif %} {#- close converted/image size comparison check #}
{%- endif %} {#- close converted size check #}
{%- endif %} {#- close root disk check #}

start_domain_{{ machine }}:
  {%- if opts['test'] %} {#- ugly workaround to virt.running failing if the VM is not yet defined #}
  test.succeed_without_changes:
    - name: Will start {{ machine }} if it is not running already
  {%- else %}
  virt.running:
    - name: {{ machine }}
    - require:
      - file: write_domainfile_{{ machine }}
      - module: define_domain_{{ machine }}
  {%- endif %}
{%- endif %} {#- close storage/image check #}

{%- endif %}
{%- endfor %}
{%- endif %}

{%- else %}

{%- do salt.log.warning('Libvirt: Skipping domain XML management due to non-primary minion ' ~ myid ~ ' in cluster ' ~ cluster) %}

{%- endif %}

{#- close domain pillar check -#}
{%- endif %}
