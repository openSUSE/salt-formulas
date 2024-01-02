{#-
Salt state file for managing utilities for the Wicked Salt states
Copyright (C) 2023-2024 Georg Pfuetzenreuter <mail+opensuse@georg-pfuetzenreuter.net>

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

{%- from 'network/wicked/map.jinja' import base_backup, script -%}

network_wicked_backup_directory:
  file.directory:
    - name: {{ base_backup }}
    - mode: '0750'

network_wicked_script:
  file.managed:
    - name: {{ script }}
    - source: salt://{{ slspath }}/files{{ script }}
    - mode: '0750'

network_wicked_script_links:
  file.symlink:
    - names:
      - {{ script }}up:
        - target: {{ script }}
      - {{ script }}down:
        - target: {{ script }}
      - {{ script }}routes:
        - target: {{ script }}
