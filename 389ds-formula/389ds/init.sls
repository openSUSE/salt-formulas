{#-
Salt state file for managing 389-DS
Copyright (C) 2026 SUSE LLC <georg.pfuetzenreuter@suse.com>

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

include:
  - .server
  - .data

{#- any more efficient way to check if we are rendering the data state? #}
{%- for name, config in salt['pillar.get']('389ds:instances', {}).items() %}
  {%- if 'data' in config %}
# when applying both server and data, data only makes sense if server succeeded
extend:
  389ds-data:
    389ds:
      - require:
          - sls: 389ds.server
   {%- endif %}
   {%- break %}
{%- endfor %}
