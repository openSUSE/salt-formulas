{#-
Salt state file for managing libvirt
Copyright (C) 2023 SUSE LLC <georg.pfuetzenreuter@suse.com>

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

{%- set libvirt_configs = ['network'] -%}
{%- set libvirt_drivers = ['network', 'qemu', 'storage-disk', 'storage-mpath'] -%}
{%- set libvirt_configpath = '/etc/libvirt/' -%}
{%- from 'libvirt/map.jinja' import config -%}

libvirt_packages:
  pkg.installed:
    - no_recommends: True
    - pkgs:
      - patterns-server-kvm_server
      - libvirt-client
      {%- for config in libvirt_configs %}
      - libvirt-daemon-config-{{ config }}
      {%- endfor %}
      {%- for driver in libvirt_drivers %}
      - libvirt-daemon-driver-{{ driver }}
      {%- endfor %}

libvirt_files:
  file.managed:
    - template: jinja
    - source: salt://{{ slspath }}/files{{ libvirt_configpath }}config.jinja
    - names:
      {%- for file in config.keys() %}
      - {{ libvirt_configpath }}{{ file ~ '.conf' }}:
        - context:
            config: {{ config.get(file, {}) }}
      {%- endfor %}

# will restart itself through socket activation
libvirt_service_stop:
  service.dead:
    - name: libvirtd.service
    - require:
      - pkg: libvirt_packages
    - onchanges:
      - file: libvirt_files

libvirt_socket_run:
  service.running:
    - name: libvirtd.socket
    - enable: True
    - reload: False
    - require:
      - pkg: libvirt_packages
      - file: libvirt_files
