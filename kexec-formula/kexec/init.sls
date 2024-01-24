{#-
Salt state file for managing Kexec
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

kexec_package:
  pkg.installed:
    - name: kexec-tools

kexec_service_enable:
  service.enabled:
    - name: kexec-load
    - require:
        - pkg: kexec_package

kexec_service_run:
  service.running:
    - name: kexec-load
    - unless: kexec -S
    - require:
        - pkg: kexec_package
        - service: kexec_service_enable
