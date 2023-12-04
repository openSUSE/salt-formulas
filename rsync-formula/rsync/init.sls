{#-
Salt state file for managing rsync
Copyright (C) 2023 Georg Pfuetzenreuter <mail+opensuse@georg-pfuetzenreuter.net>
Copyright (C) 2023 SUSE LLC

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

{%- from 'rsync/map.jinja' import config, contents %}

rsync_package:
  pkg.installed:
    - names:
      - rsync

{%- if 'rsync' in pillar %}
rsyncd_config:
  file.managed:
    - names:
      - /etc/rsyncd.conf:
        - mode: '0640'
        - contents: |
            {{ pillar.get('managed_by_salt_formula', '# Managed by the rsync formula') | indent(12) }}
            # Salt managed defaults
            {{ contents(config.get('defaults', {})) }}

            # Salt managed modules
            {% for module, module_config in config.get('modules', {}).items() %}
            [{{ module }}]{{ contents(module_config) | indent(4) }}
            {%- endfor %}
      - /etc/rsyncd.secrets:
        - mode: '0600'
        - contents: |
            {{ pillar.get('managed_by_salt_formula', '# Managed by the rsync formula') | indent(12) }}
            # Salt managed users
            {{ contents(config.get('users', {}), ':') }}

rsyncd_socket:
  service.running:
    - name: rsyncd.socket
    - enable: true
    - require:
      - pkg: rsync_package
    - require:
      - rsyncd_service
{%- else %}

rsyncd_socket:
  service.dead:
    - name: rsyncd.socket
    - enable: false
{%- endif %}

rsyncd_service:
  service.dead:
    - name: rsyncd.service
    - enable: false
    {%- if 'rsync' in pillar %}
    - watch:
      - file: rsyncd_config
    {%- endif %}
