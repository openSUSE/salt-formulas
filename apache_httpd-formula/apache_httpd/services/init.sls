{#-
Salt state file for managing the Apache HTTP server service
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

include:
  - apache_httpd.packages
  - .watch

apache_httpd_service:
  service.running:
    - name: apache2
    - enable: True
    - reload: True
    - require:
        - pkg: apache_httpd_packages
    - require_in:
        - module: apache_httpd_service_restart
