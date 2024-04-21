{#-
Salt state file for managing the Apache HTTP server on openSUSE and SLES
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

{%- from 'apache_httpd/map.jinja' import httpd, modules, mpm, places, sysconfig, cmd_kwargs -%}

{%- if salt['file.access']('/usr/sbin/a2enmod', 'x') %}
{%- set have_a2enmod = True %}
{%- set try_a2enmod = True %}
{%- else %}
{%- set have_a2enmod = False %}
{#- if apache2 is not yet installed, states using a2enmod fail in test mode #}
{%- set try_a2enmod = not opts['test'] %}
{%- endif %}

{#- no native is-active implementation in modules.systemd_service,
    this was deemed better than reading the (potentially big) service.get_running list
#}
{%- if salt['cmd.retcode']('/usr/bin/systemctl is-active apache2', **cmd_kwargs) == 0 %}
  {%- macro watch_in_restart() %}
    - watch_in:
        - module: apache_httpd_service_restart
  {%- endmacro %}
{%- else %}
  {%- macro watch_in_restart() %}
    {#- noop #}
  {%- endmacro %}
{%- endif %}

include:
  - .packages
  - .services
{%- if httpd.purge %}
  - .purge
{%- endif %}

apache_httpd_sysconfig:
  suse_sysconfig.sysconfig:
    - name: apache2
    - key_values:
        {%- for key, value in sysconfig.items() %}
        {{ key }}: '"{{ value }}"'
        {%- endfor %}
    - require:
        - pkg: apache_httpd_packages
    - watch_in:
        - service: apache_httpd_service

{%- if try_a2enmod %}
{%- for module in modules %}
apache_httpd_load_module-{{ module }}:
  module.run:
    - apache.a2enmod:
        - mod: {{ module }}
    - require:
        - pkg: apache_httpd_packages
    - require_in:
        {%- for place in places %}
        - file: apache_httpd_{{ place }}
        {%- endfor %}
    - unless:
        - fun: apache.check_mod_enabled
          mod: {{ module }}
    {{ watch_in_restart() }}
{%- endfor %} {#- close configured modules loop #}
{%- endif %} {#- close a2enmod check #}

{%- if have_a2enmod %}
{%- for module in salt['cmd.run_stdout']('/usr/sbin/a2enmod -l', **cmd_kwargs).split() %}
  {%- if module not in modules %}
apache_httpd_unload_module-{{ module }}:
  module.run:
    - apache.a2dismod:
        - mod: {{ module }}
    - require_in:
        {%- for place in places %}
        - file: apache_httpd_{{ place }}
        {%- endfor %}
    {{ watch_in_restart() }}
  {%- endif %}
{%- endfor %} {#- close enabled modules loop #}
{%- endif %} {#- close a2enmod check #}

{%- for place in places %}
  {%- set directory = httpd.directories[place] %}
  {%- set config_pillar = httpd.get(place, {}) %}
  {%- if config_pillar %}
apache_httpd_{{ place }}:
  file.managed:
    - names:
        {%- for config, settings in config_pillar.items() %}
        - {{ directory }}/{{ config }}.conf:
            - context:
                name: {{ config }}
                config: {{ settings }}
                type: {{ place }}
                repetitive_options: {{ httpd.internal.repetitive_options }}
                logdir: {{ httpd.directories.logs }}
                wwwdir: {{ httpd.directories.htdocs }}
        {%- endfor %}
    - source: salt://apache_httpd/templates/config.jinja
    - template: jinja
    - check_cmd: apachectl -tf
    {#- setting this tmp_dir is marginally better than the default - the minion users home directory (usually /root/)
        a mktemp like directory would be ideal, but creating one using modules.temp in Jinja would leave it behind after the state run
    #}
    - tmp_dir: /dev/shm
    - require:
        - pkg: apache_httpd_packages
    - watch_in:
        - service: apache_httpd_service
  {%- endif %} {#- close pillar check #}
{%- endfor %} {#- close places loop #}
