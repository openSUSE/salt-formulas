{#-
Salt state file for managing TAYGA
Copyright (C) 2023 Georg Pfuetzenreuter <mail+opensuse@georg-pfuetzenreuter.net>

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

{%- set tayga = salt.pillar.get('tayga', {}) %}

tayga_package:
  pkg.installed:
    - name: tayga

{%- if tayga %}
tayga_configuration:
  file.managed:
    - name: /etc/tayga.conf
    - source: salt://{{ slspath }}/files/etc/tayga.conf.j2
    - template: jinja
    - context:
        tayga: {{ tayga }}

tayga_service:
  service.running:
    - name: tayga
    - enable: true
    - reload: false
    - require:
      - pkg: tayga_package
    - watch:
      - file: tayga_configuration
{%- endif %}
