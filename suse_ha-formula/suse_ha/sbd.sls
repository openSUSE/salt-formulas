{#-
Salt state file for managing SBD devices
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

{%- from 'suse_ha/map.jinja' import sbd, sysconfig, is_primary -%}
{%- if 'devices' in sbd %}
include:
  - .packages

{%- set devices = sbd['devices'] -%}
{%- set cmd_base = 'sbd' -%}
{%- set sbd_ns = namespace(deviceargs='', timeoutargs='', devices='') -%}

{%- for device in devices -%}
{%- set sbd_ns.deviceargs = sbd_ns.deviceargs ~ ' -d ' ~ device -%}
{%- endfor -%}
{%- set sbd_ns.devices = devices | join(';') -%}

{%- if 'timeouts' in sbd -%}
{%- set timeout_msgwait = sbd.timeouts.get('msgwait', False) -%}
{%- if timeout_msgwait -%}
{%- set sbd_ns.timeoutargs = sbd_ns.timeoutargs ~ ' -4 ' ~ timeout_msgwait -%}
{%- endif -%}
{%- set timeout_watchdog = sbd.timeouts.get('watchdog', False) -%}
{%- if timeout_watchdog -%}
{%- set sbd_ns.timeoutargs = sbd_ns.timeoutargs ~ ' -1 ' ~ timeout_watchdog -%}
{%- endif -%}
{%- endif -%} {#- close timeouts check -#}

{%- set cmd_base = cmd_base ~ ' ' ~ sbd_ns.deviceargs ~ ' ' -%}
{%- set cmd_format = cmd_base ~ sbd_ns.timeoutargs ~ ' create' -%}
{%- set cmd_check = cmd_base ~ ' dump' -%}

{%- do salt.log.debug('suse_ha: constructed SBD cmd_format: ' ~ cmd_format) -%}
{%- do salt.log.debug('suse_ha: constructed SBD cmd_check: ' ~ cmd_check) %}

{%- if is_primary %}
sbd_shutdown:
  service.dead:
    - name: corosync
    - prereq:
      - cmd: sbd_format_devices
    - require:
      - suse_ha_packages

sbd_format_devices:
  cmd.run:
    - name: {{ cmd_format }}
    {%- if not sbd.get('reconfigure', False) %}
    - unless: {{ cmd_check }}
    {%- endif %}
    - require:
      - suse_ha_packages
{%- else %}
{%- do salt.log.debug('suse_ha: skipping SBD device creation on non-primary node') -%}
{%- endif %}

sbd_sysconfig:
  suse_sysconfig.sysconfig:
    - name: sbd
    - uncomment: '#'
    - quote: False
    - key_values:
        SBD_DEVICE: {{ sbd_ns.devices }}
        {%- if sysconfig.get('sbd', False) %}
        {%- for key, value in sysconfig.sbd.items() %}
        {{ key }}: {{ value }}
        {%- endfor %}
        {%- endif %}
    - require:
      - suse_ha_packages

sbd_service:
  service.enabled:
    - name: sbd
    - require:
      - suse_ha_packages
      {%- if is_primary %}
      - cmd: sbd_format_devices
      {%- endif %}
      - suse_sysconfig: sbd_sysconfig

{%- else %}
{%- do salt.log.error('suse_ha: sbd.devices called with no devices in the pillar') -%}
{%- endif %} {#- close devices check -#}
