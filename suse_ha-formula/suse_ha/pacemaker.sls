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

{%- from slspath ~ '/map.jinja' import cluster, fencing, management, sysconfig -%}
{%- from slspath ~ '/macros.jinja' import primitive_resource, rsc_default, ipmi_secret -%}
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
    {% if fencing.enable and fencing['stonith_enabled']
      and (salt['mine.get'](cluster.name ~ '*', 'network.get_hostname', tgt_type='compound') | length()) >= 2 %}
    - name: crm configure property stonith-enabled=true
    - unless: test $(crm configure get_property stonith-enabled) == 'true'
    {% else %}
    - name: crm configure property stonith-enabled=false
    - unless: test $(crm configure get_property stonith-enabled) == 'false'
    {% endif %}
    - require:
      - pacemaker.service

{% if fencing.enable and fencing['stonith_enabled'], False == True %}
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
{{ rsc_default('failure-timeout') }}
{{ rsc_default('migration-threshold') }}

{%- endif -%}

{{ rsc_default('allow-migrate') }}

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

{%- if fencing.enable and 'ipmi' in fencing %}
{%- for host, config in fencing.ipmi.hosts.items() %}
{%- set instance_attributes = {
      'hostname': host, 'ipaddr': config['ip'], 'passwd': '/etc/pacemaker/ha_ipmi_' ~ host, 'userid': config['user'],
      'interface': config['interface'], 'passwd_method': 'file', 'ipmitool': '/usr/bin/ipmitool', 'priv': config['priv'] } %}

{{ primitive_resource(host, class='stonith', type='external/ipmi', instance_attributes=instance_attributes,
                      operations=fencing.ipmi.primitive.operations, meta_attributes=fencing.ipmi.primitive.meta_attributes) }}

{{ ipmi_secret(host, config['secret'], True) }}

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
  - .packages
  - .resources

{%- else %}
{%- do salt.log.info('Not sending any Pacemaker configuration - ' ~ myfqdn ~ ' is not the designated controller.') -%}

{%- if fencing.enable and 'ipmi' in fencing %}
{%- for host, config in fencing.ipmi.hosts.items() %}
{{ ipmi_secret(host, config['secret'], False) }}
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
{%- if sysconfig.pacemaker | length %}
    - watch:
      - file: /etc/sysconfig/pacemaker
  file.keyvalue:
    - name: /etc/sysconfig/pacemaker
    - separator: '='
    - show_changes: True
    - key_values:
        {%- for key, value in sysconfig.pacemaker.items() %}
        '{{ key }}': '"{{ value }}"'
        {%- endfor %}
    - require:
      - suse_ha_packages
{%- endif %}
{%- else %}
{%- do salt.log.error('suse_ha: cluster pillar not configured, not enabling Pacemaker!') %}
{%- endif %}
