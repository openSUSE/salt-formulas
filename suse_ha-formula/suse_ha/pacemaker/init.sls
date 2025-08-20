{#-
Salt state file for managing Pacemaker
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

{%- from 'suse_ha/map.jinja' import cluster, cmd_kwargs, fencing, is_standby, sysconfig -%}
{%- from 'suse_ha/macros.jinja' import ha_resource, property, rsc_default, ipmi_secret -%}
{%- set myfqdn = grains['fqdn'] -%}
{%- set myhost = grains['host'] -%}
{%- if salt['cmd.has_exec']('/usr/sbin/crmadmin') -%}
  {%- set clusterdc = salt['cmd.run']('/usr/sbin/crmadmin -q -D 1', **cmd_kwargs) -%}
{%- else -%}
  {%- do salt.log.error('crmadmin is not available!') -%}
  {%- set clusterdc = None -%}
{%- endif -%}

{% if myfqdn == clusterdc or myhost == clusterdc %}
{#- to-do: the crm script generates the XML but fails to patch the config with "name 'cibadmin_opt' is not defined" - bug?
{{ property('default-resource-stickiness', 1000) }}
#}

{%- if fencing.enable and fencing.get('stonith_enable', False)
  and (salt['mine.get'](cluster.name ~ '*', 'network.get_hostname', tgt_type='compound') | length()) >= 2 %}
{{ property('stonith-enabled', 'true') }}
{% else %}
{{ property('stonith-enabled', 'false') }}
{% endif %}

{%- if fencing.enable and fencing['stonith_enabled'], False == True %}
{{ property('no-quorum-policy') }}

{#-
optional resource meta configuration
https://clusterlabs.org/pacemaker/doc/deprecated/en-US/Pacemaker/1.1/html/Pacemaker_Explained/s-resource-options.html
-#}
{{ rsc_default('failure-timeout') }}
{{ rsc_default('migration-threshold') }}

{%- endif -%}

{{ property('batch-limit') }}
{{ property('migration-limit') }}
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

{#- to-do: figure out if these values make sense #}
{#- to-do: allow override using pillar #}
{%- set utilization_meta_attributes = {'target-role': 'Started'} %}
{%- set utilization_operations = {
      'start': {'interval': 0, 'timeout': 90},
      'stop': {'interval': 0, 'timeout': 100},
      'monitor': {'interval': '60s', 'timeout': '20s'}
} %}

{{ ha_resource('p-node-utilization', class='ocf', type='NodeUtilization', instance_attributes={}, provider='pacemaker',
                      meta_attributes=utilization_meta_attributes, operations=utilization_operations,
                      clone={ 'resource_id': 'c-node-utilization', 'meta_attributes': {'target-role': 'Started', 'interleave': 'true'} }) }}

include:
  - suse_ha.packages
{%- if fencing.enable %}
{%- if 'ipmi' in fencing %}
  - .fencing.external_ipmi
{%- endif %}
{%- if 'sbd' in fencing %}
  - .fencing.external_sbd
{%- endif %}
{%- endif %}
  - suse_ha.resources
  - suse_ha.restart

{%- else %}
{%- do salt.log.info('Not sending any Pacemaker configuration - ' ~ myfqdn ~ ' is not the designated controller.') -%}

include:
  - suse_ha.restart

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
    - reload: False
    - retry:
        attempts: 3
        interval: 10
        splay: 5
    - require:
      - suse_ha_packages
      - corosync.service
{%- if sysconfig.pacemaker | length %}
  suse_sysconfig.sysconfig:
    - name: /etc/sysconfig/pacemaker
    - header_pillar: managed_by_salt_formula_sysconfig
    - uncomment: '# '
    - upper: False
    - quote_booleans: False
    - key_values:
        {%- for key, value in sysconfig.pacemaker.items() %}
        {{ key }}: {{ value }}
        {%- endfor %}
    - require:
      - suse_ha_packages
    - watch_in:
      - cmd: suse_ha_restart
{%- endif %}
{%- else %}
{%- do salt.log.error('suse_ha: cluster pillar not configured, not enabling Pacemaker!') %}
{%- endif %}
