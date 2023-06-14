{#-
Salt state file for managing multipath
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

include:
  - .packages

multipath_config:
  file.managed:
    - name: /etc/multipath.conf
    - source: salt://{{ slspath }}/files/etc/multipath.conf.jinja
    - template: jinja
    - require:
      - pkg: multipath_packages

multipath_service:
  service.dead:
    - name: multipathd.service
    - onchanges:
      - file: multipath_config
    - require:
      - pkg: multipath_packages

multipath_socket:
  service.running:
    - name: multipathd.socket
    - enable: true
    - require:
      - pkg: multipath_packages
      - file: multipath_config
