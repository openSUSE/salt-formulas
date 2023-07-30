{#-
Salt state file for managing IPMI fencing resources
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

{%- from slspath ~ '/../../map.jinja' import fencing -%}
{%- from slspath ~ '/../../macros.jinja' import ha_resource, ipmi_secret -%}
{%- set fencing_ipmi = fencing.get('ipmi', {}) -%}

{%- if 'hosts' in fencing_ipmi %}
{%- for host, config in fencing_ipmi.hosts.items() %}

{%- set instance_attributes = {
      'hostname': host, 'ipaddr': config['ip'], 'passwd': '/etc/pacemaker/ha_ipmi_' ~ host, 'userid': config['user'],
      'interface': config['interface'], 'passwd_method': 'file', 'ipmitool': '/usr/bin/ipmitool', 'priv': config['priv'] } %}

{%- if 'port' in config %}
{%- do instance_attributes.update({'ipport': config['port']}) -%}
{%- endif %}

{{ ha_resource(host, class='stonith', type='external/ipmi', instance_attributes=instance_attributes,
                      operations=fencing.ipmi.primitive.operations, meta_attributes=fencing.ipmi.primitive.meta_attributes) }}

{{ ipmi_secret(host, config['secret'], True) }}

{%- endfor %}
{%- else %}
{%- do salt.log.error('suse_ha: pacemaker.fencing.external_ipmi called, but no hosts defined in pillar') -%}
{%- endif %}
