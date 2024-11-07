{#-
Salt state file for managing /etc/hosts
Copyright (C) 2024 Georg Pfuetzenreuter <mail+opensuse@georg-pfuetzenreuter.net>
Copyright (C) 2024 SUSE LLC <georg.pfuetzenreuter@suse.com>

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

/etc/hosts:
  file.managed:
    - source: salt://{{ 'infrastructure/' if salt['pillar.get']('infrastructure:hosts') else '' }}hosts/files/hosts.j2
    - template: jinja
    - mode: '0644'
    - user: root
    - group: root
