{#-
Salt state file for managing multipath
Copyright (C) 2024 Georg Pfuetzenreuter <mail+opensuse@georg-pfuetzenreuter.net>
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

include:
  - .packages

multipath_config:
  file.managed:
    - name: /etc/multipath.conf
    - source: salt://{{ slspath }}/files/etc/multipath.conf.jinja
    - template: jinja
    - require:
      - pkg: multipath_packages

multipath_service_reload:
  module.run:
    - name: service.reload
    - m_name: multipathd
    - onchanges:
      - file: multipath_config
    - onlyif:
      - fun: service.status
        name: multipathd
    - require:
      - pkg: multipath_packages

{%- if grains['osrelease'] | float > 15.5 %}
multipath_service:
  service.running:
    - name: multipathd
    - enable: true
    - require:
      - pkg: multipath_packages
      - file: multipath_config

multipath_socket:
  service.dead:
    - name: multipathd.socket

{%- else %}

multipath_socket:
  service.running:
    - name: multipathd.socket
    - enable: true
    - require:
      - pkg: multipath_packages
      - file: multipath_config
{%- endif %}
