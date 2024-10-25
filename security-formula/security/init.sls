{#-
Salt state file for managing permissions
Copyright (C) 2024 Georg Pfuetzenreuter <mail+opensuse@georg-pfuetzenreuter.net>

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
{%- set mypillar    = pillar.get('security', {}) -%}
{%- set permissions = mypillar.get('permissions', {}) -%}
{%- set sysconfig   = mypillar.get('sysconfig', {}) -%}

security_permissions_zypp_hook:
{%- if permissions %}
  pkg.installed:
{%- else %}
  pkg.removed:
{%- endif %}
    - name: permissions-zypp-plugin

security_permissions_local:
  file.managed:
    - name: /etc/permissions.local
    - source: salt://{{ slspath }}/files/etc/permissions.local.jinja
    - template: jinja
    - context:
        permissions: {{ permissions }}

security_sysconfig:
  suse_sysconfig.sysconfig:
    - name: security
    - key_values:
        PERMISSION_SECURITY: '{{ sysconfig.get('permission_security', 'secure') }} local'
        PERMISSION_FSCAPS: '{{ sysconfig.get('permission_fscaps', '') }}'
        {%- for key, value in mypillar.items() %}
          {%- if key | lower not in ['permission_security', 'permission_fscaps'] %}
        {{ key }}: {{ value }}
          {%- endif %}
        {%- endfor %}


security_apply:
  cmd.run:
    - name: chkstat --noheader --system
    - onlyif:
        - fun: cmd.run_stdout
          cmd: chkstat --noheader --system --warn
    - require:
        - file: security_permissions_local
        - suse_sysconfig: security_sysconfig
