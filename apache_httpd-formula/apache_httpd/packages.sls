{#-
Salt state file for managing the Apache HTTP server packages
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

{%- from 'apache_httpd/map.jinja' import httpd, modules, mpm -%}

apache_httpd_packages:
  pkg.installed:
    - pkgs:
        - apache2-{{ mpm }}
        {%- for module in modules %}
          {%- if module not in httpd.internal.modules.base and module != 'cgi' %}
        - apache2-mod_{{ module }}
          {%- endif %}
        {%- endfor %}
        - apache2-utils
        # https://bugzilla.opensuse.org/show_bug.cgi?id=1226379
        - apache2
