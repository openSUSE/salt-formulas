{#-
Salt state file for managing SBD fencing resources
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
{%- from slspath ~ '/../../macros.jinja' import ha_resource -%}
{%- set fencing_sbd = fencing.get('sbd', {}) -%}
{%- set instance_defaults = fencing_sbd.get('defaults', {}) -%}
{%- set attributes = ['pcmk_host_list', 'pcmk_delay_base', 'pcmk_delay_max'] %}

include:
  - suse_ha.sbd

{%- if 'instances' in fencing_sbd %}
{%- for instance, config in fencing_sbd.instances.items() %}
{%- set instance_attributes = {} -%}

{%- for attribute in attributes %}
{%- if attribute in config %}
{%- do instance_attributes.update({attribute: config[attribute]}) -%}
{%- elif attribute in instance_defaults -%}
{%- do instance_attributes.update({attribute: instance_defaults[attribute]}) -%}
{%- endif %}
{%- endfor %}

{{ ha_resource('sbd-' ~ instance, class='stonith', type='external/sbd', instance_attributes=instance_attributes, operations=fencing.sbd.primitive.operations, requires=['service: sbd_service']) }}

{%- endfor %}
{%- else %}
{%- do salt.log.error('suse_ha: pacemaker.fencing.external_sbd called, but no instances defined in pillar') -%}
{%- endif %}
