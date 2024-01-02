{#-
Salt state file for managing Gitea
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

{%- from 'gitea/map.jinja' import config %}

gitea_package:
  pkg.installed:
    - name: gitea

gitea_configuration:
  ini.options_present:
    - name: /etc/gitea/conf/app.ini
    - strict: True
    - sections:
      {%- for section in config.keys() %}
        {{ section | upper if section == 'default' else section }}:
        {%- for option, value in config[section].items() %}
          {{ option | upper }}: {{ value }}
        {%- endfor %}
      {%- endfor %}
    - require:
      - pkg: gitea_package

gitea_service:
  service.running:
    - name: gitea
    - enable: True
    - require:
      - pkg: gitea_package
    - watch:
      - ini: gitea_configuration
