{#-
Salt state file for managing Jenkins Controllers
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

{%- from 'jenkins/map.jinja' import controller -%}

jenkins_controller_packages:
  pkg.installed:
    - pkgs:
      - jenkins
      - jenkins-plugin-configuration-as-code

jenkins_controller_sysconfig:
  file.keyvalue:
    - name: /etc/sysconfig/jenkins
    - key_values:
      {%- for k, v in controller.sysconfig.items() %}
        {{ k | upper }}: '"{{ v }}"'
      {%- endfor %}
    - ignore_if_missing: {{ opts['test'] }}
    - append_if_not_found: True
    - require:
      - pkg: jenkins_controller_packages

jenkins_controller_config_directory:
  file.directory:
    - name: /etc/jenkins
    - group: jenkins
    - require:
      - pkg: jenkins_controller_packages

{%- if 'config' in controller %}
jenkins_controller_config_file:
  file.serialize:
    - name: /etc/jenkins/salt.yaml
    - serializer: yaml
    - dataset: {{ controller.config }}
    - group: jenkins
    - mode: '0640'
    - require:
      - pkg: jenkins_controller_packages
      - file: jenkins_controller_config_directory
{%- else %}
{%- do salt.log.warning('jenkins.controller: no JCasC configuration defined') -%}
{%- endif %}

jenkins_controller_service:
  service.running:
    - name: jenkins
    - enable: True
    - watch: # graceful reload possible ?
      - file: jenkins_controller_sysconfig
      - file: jenkins_controller_config_file
    - require:
      - pkg: jenkins_controller_packages
