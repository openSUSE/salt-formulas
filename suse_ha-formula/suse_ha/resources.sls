{#-
Salt state file for managing SUSE HA cluster resources
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

{%- from 'suse_ha/map.jinja' import constraints, resources, resources_dir -%}
{%- from 'suse_ha/macros.jinja' import ha_constraint, ha_resource -%}

ha_resources_directory:
  file.directory:
    - name: {{ resources_dir }}
    - mode: '0755'

{#- custom resources if defined in the suse_ha:resources pillar #}
{%- if resources is defined and resources is not none and resources | length > 0 %}
{%- for resource, config in resources.items() %}
{%- if not 'type' in config -%}{%- do salt.log.error('Resource ' ~ resource ~ ' is missing "type"') -%}{%- endif %}
{{ ha_resource(
    resource, config.get('class', 'ocf'), config.get('type', None),
    config.get('attributes', {}), config.get('operations', {}), config.get('meta_attributes', {}), config.get('provider', 'heartbeat'),
    config.get('clone', {})) }}
{%- endfor %}
{%- else %}
{%- do salt.log.debug('Skipping construction of custom resources') %}
{%- endif %}

{%- for constraint, config in constraints.items() %}
{{ ha_constraint(
      constraint,
      config.get('type'),
      config.get('kind'),
      config.get('score'),
      config.get('resources', []),
      config.get('sets', {}),
    )
}}
{%- endfor %}
