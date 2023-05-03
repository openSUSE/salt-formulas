{#-
Salt state file for managing SUSE HA cluster resources
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

{%- from slspath ~ '/map.jinja' import resources, resources_dir -%}
{%- from slspath ~ '/macros.jinja' import primitive_resource -%}

ha_resources_directory:
  file.directory:
    - name: {{ resources_dir }}
    - mode: '0755'

{#- custom resources if defined in the suse_ha:resources pillar #}
{%- if resources is defined and resources is not none and resources | length > 0 %}
{%- for resource, config in resources.items() %}
{{ primitive_resource(resource, config['class'], config['type'], config['attributes'], config['operations'], config['meta_attributes']) }}
{%- endfor %}
{%- else %}
{%- do salt.log.debug('Skipping construction of custom resources') %}
{%- endif %}
