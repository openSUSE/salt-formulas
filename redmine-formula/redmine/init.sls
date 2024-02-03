{#-
Salt state file for managing Redmine
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
#}

{%- from 'redmine/map.jinja' import config, plugins %}

redmine_packages:
  pkg.installed:
    - pkgs:
      - redmine
      {%- for plugin in plugins %}
      - redmine-{{ plugin }}
      {%- endfor %}

redmine_update:
  cmd.run:
    - name: redmine-update
    - use_vt: True
    - onchanges:
      - pkg: redmine_packages

{%- for file in ['configuration', 'database'] %}
{%- if file in config %}
redmine_file_{{ file }}:
  file.serialize:
    - dataset: {{ config[file] }}
    - name: /etc/redmine/{{ file }}.yml
    - serializer: yaml
    - group: redmine
    - mode: '0640'
    - require:
      - pkg: redmine_packages
    - watch_in:
      - service: redmine_service
{%- endif %}
{%- endfor %}

redmine_service:
  service.running:
    - names:
      - redmine
      - redmine-sidekiq
    - enable: True
    - require:
      - pkg: redmine_packages
