{#-
Salt state file for managing Pacemaker
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

{%- from slspath ~ '/map.jinja' import cluster, fencing, management -%}
{%- from slspath ~ '/macros.jinja' import primitive_resource -%}
{%- set myfqdn = grains['fqdn'] -%}
{%- set myhost = grains['host'] -%}
{%- if salt['cmd.retcode']('test -x /usr/sbin/crmadmin') == 0 -%}
{%- set clusterdc = salt['cmd.run']('/usr/sbin/crmadmin -q -D 1') -%}
{%- else -%}
{%- do salt.log.error('crmadmin is not available!') -%}
{%- set clusterdc = None -%}
{%- endif -%}

{% if myfqdn == clusterdc or myhost == clusterdc %}
{#- to-do: the crm script generates the XML but fails to patch the config with "name 'cibadmin_opt' is not defined" - bug?
ha_default_resource_stickiness:
  cmd.run:
    - name: crm configure property default-resource-stickiness=1000
    - unless: test $(crm configure get_property default-resource-stickiness) gt 0
    - require:
      - pacemaker.service
#}

ha_setup_stonith:
  cmd.run:
    {% if fencing['stonith_enabled'], False
      and (salt['mine.get'](cluster.name ~ '*', 'network.get_hostname', tgt_type='compound') | length()) >= 2 %}
    - name: crm configure property stonith-enabled=true
    - unless: test $(crm configure get_property stonith-enabled) == 'true'
    {% else %}
    - name: crm configure property stonith-enabled=false
    - unless: test $(crm configure get_property stonith-enabled) == 'false'
    {% endif %}
    - require:
      - pacemaker.service

{% if fencing['stonith_enabled'], False == True %}
{%- if 'no_quorum_policy' in management %}
ha_default_quorum_policy:
  cmd.run:
    - name: 'crm configure property no-quorum-policy={{ management.no_quorum_policy }}'
    - unless: 'test $(crm configure get_property no-quorum-policy) == {{ management.no_quorum_policy }}'
    - require:
      - pacemaker.service
{%- endif %}

{#-
optional resource meta configuration
https://clusterlabs.org/pacemaker/doc/deprecated/en-US/Pacemaker/1.1/html/Pacemaker_Explained/s-resource-options.html
-#}
{%- if 'failure_timeout' in management %}
ha_default_failure_timeout:
  cmd.run:
    - name: 'crm configure rsc_defaults failure-timeout={{ management.failure_timeout }}'
    - unless: 'test $(crm_attribute -t rsc_defaults -G -n failure-timeout -q) == {{ management.failure_timeout }}'
    - require:
      - pacemaker.service
{%- endif %}

{%- if 'migration_threshold' in management %}
ha_default_migration_threshold:
  cmd.run:
    - name: 'crm configure rsc_defaults migration-threshold={{ management.migration_threshold }}'
    - unless: 'test $(crm_attribute -t rsc_defaults -G -n migration-threshold -q) == {{ management.migration_threshold }}'
    - require:
      - pacemaker.service
{%- endif %}

{%- endif -%}

{%- if 'allow_migrate' in management %}
ha_default_allow_migrate:
  cmd.run:
    - name: 'crm configure rsc_defaults allow-migrate={{ management.allow_migrate }}'
    - unless: 'test $(crm_attribute -t rsc_defaults -G -n allow-migrate -q) == {{ management.allow_migrate }}'
    - require:
      - pacemaker.service
{%- endif %}

{#-
we currently don't use this
ha_add_admin_ip:
  cmd.run:
    - name: 'crm configure primitive admin_addr IPaddr2 params ip={{ management.adm_ip }} op monitor interval=10 timeout=20'
    # untested
    - unless: 'test $(crm -Dplain configure show admin_addr | grep -oP "ip=\K(.*)") == {{ management.adm_ip }}'
    - require:
      - pacemaker.service
      - ha_setup_stonith
-#}

{%- if 'ipmi' in fencing %}
{%- for host, config in fencing.ipmi.hosts.items() %}
{%- set instance_attributes = {
      'hostname': host, 'ipaddr': config['ip'], 'passwd': '/etc/pacemaker/ha_ipmi_' ~ host, 'userid': config['user'],
      'interface': config['interface'], 'passwd_method': 'file', 'ipmitool': '/usr/bin/ipmitool', 'priv': config['priv'] } %}
{%- set operations = {
      'start': {'timeout': 20, 'interval': 0}, 'stop': {'timeout': 15, 'interval': 0}, 'monitor': {'timeout': 20, 'interval': 3600} } %}
{%- set meta_attributes = {
      'target-role': 'Started' } %}

{{ primitive_resource(host, class='stonith', type='external/ipmi',
                      instance_attributes=instance_attributes, operations=operations, meta_attributes=meta_attributes) }}

ha_fencing_ipmi_secret_{{ host }}:
  file.managed:
    - name: /etc/pacemaker/ha_ipmi_{{ host }}
    - contents: '{{ config['secret'] }}'
    - contents_newline: False
    - mode: '0600'
    - require:
      - suse_ha_packages
    - require_in:
      - ha_resource_file_{{ host }}
      - ha_resource_update_{{ host }}
{%- endfor %}
{%- endif %}

{#- to-do: figure out if these values make sense #}
ha_add_node_utilization_primitive:
  cmd.run:
    - name: crm configure primitive p-node-utilization ocf:pacemaker:NodeUtilization op start timeout=90 interval=0 op stop timeout=100 interval=0 op monitor timeout=20s interval=60s meta target-role=Started
    - unless: crm resource list p-node-utilization
    - require:
      - pacemaker.service

ha_add_node_utilization_clone:
  cmd.run:
    - name: crm configure clone c-node-utilization p-node-utilization meta target-role=Started
    - unless: crm resource list c-node-utilization
    - require:
      - pacemaker.service
      - ha_add_node_utilization_primitive

include:
  - .resources

{%- else %}
{%- do salt.log.info('Not sending any Pacemaker configuration - ' ~ myfqdn ~ ' is not the designated controller.') -%}

{%- if 'ipmi' in fencing %}
{%- for host, config in fencing.ipmi.hosts.items() %}
ha_fencing_ipmi_secret_{{ host }}:
  file.managed:
    - name: /etc/pacemaker/ha_ipmi_{{ host }}
    - contents: '{{ config['secret'] }}'
    - contents_newline: False
    - mode: '0600'
    - require:
      - suse_ha_packages
{%- endfor %}
{%- endif %}

{%- endif %}

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
  file.keyvalue:
    - name: /etc/sysconfig/pacemaker
    - separator: '='
    - show_changes: True
    - key_values:
        'LRMD_MAX_CHILDREN': '"4"'
    - require:
      - suse_ha_packages
{%- else %}
{%- do salt.log.error('suse_ha: cluster pillar not configured, not enabling Pacemaker!') %}
{%- endif %}
