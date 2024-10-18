{#-
Salt state file for managing doofetch
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

{%- set mypillar = salt['pillar.get']('doofetch', {}) %}
{%- set mykey = mypillar.get('gpg', {}).get('key', {}) %}

{%- if mykey and 'url' in mykey and 'fingerprint' in mykey %}
doofetch_repository_key:
  cmd.run:
    - name: gpg --import < <(curl -sS {{ mykey['url'] }})
    - shell: /bin/bash
    - unless:
        - gpg --list-key {{ mykey['fingerprint'] }}
        - '! gpg --list-key {{ mykey['fingerprint'] }} | grep expired'
{%- endif %}

doofetch_package:
  pkg.installed:
    - name: doofetch

{%- if 'sysconfig' in mypillar and mypillar['sysconfig'] is mapping %}
doofetch_sysconfig:
  suse_sysconfig.sysconfig:
    - name: /etc/sysconfig/doofetch
    - quote_char: "'"
    - key_values: {{ mypillar['sysconfig'] }}
    - require:
        - pkg: doofetch_package
{%- endif %}

doofetch_timer:
  service.running:
    - name: doofetch.timer
    - enable: true
    - require:
        - pkg: doofetch_package
