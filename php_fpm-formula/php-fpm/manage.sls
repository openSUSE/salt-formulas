{#-
Salt state file for managing PHP FPM
Copyright (C) 2025 Georg Pfuetzenreuter <mail+opensuse@georg-pfuetzenreuter.net>

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

{%- from 'php-fpm/map.jinja' import etcfpm, php, pools %}

php-fpm_package:
  pkg.installed:
    - name: {{ php }}-fpm

php-fpm_config:
  file.managed:
    - names:
        - {{ etcfpm }}php-fpm.conf:
            - contents:
                - {{ pillar.get('managed_by_salt_formula_ini', '; Managed by the PHP-FPM formula') | yaml_encode }}
                - include={{ etcfpm }}php-fpm.d/salt.conf
        - {{ etcfpm }}php-fpm.d/salt.conf:
            - source: salt://php-fpm/templates/pool.conf.jinja
            - template: jinja
            - context:
                pools: {{ pools }}
    - require:
        - pkg: php-fpm_package

{%- for file in salt['file.find'](etcfpm ~ 'php-fpm.d', mindepth=1, print='name') %}
  {%- if
        file not in ['salt.conf', 'www.conf.default']
        and
        file.replace('.conf', '') not in pools 
  %}
php-fpm_config_delete_{{ file }}:
  file.absent:
    - name: {{ etcfpm ~ 'php-fpm.d/' ~ file }}
    - watch_in:
        - service: php-fpm_service
  {%- endif %}
{%- endfor %}

{%- for dir in salt['file.find']('/etc', maxdepth=1, mindepth=1, name='php*', print='name', type='d') %}
  {%- if dir != php %}
php-fpm_config_delete_{{ dir }}:
  file.absent:
    - name: /etc/{{ dir }}/fpm
  {%- endif %}
{%- endfor %}

php-fpm_service:
  service.running:
    - name: php-fpm
    - enable: true
    - reload: true
    - watch:
        - file: php-fpm_config
    - require:
        - pkg: php-fpm_package
