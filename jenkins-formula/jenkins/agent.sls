{#-
Salt state file for managing Jenkins Agents
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

{%- from 'jenkins/map.jinja' import agent -%}

jenkins_agent_packages:
  pkg.installed:
    - name: jenkins-agent

{%- if 'sysconfig' in agent %}
jenkins_agent_sysconfig:
  suse_sysconfig.sysconfig:
    - name: jenkins-agent
    - header_pillar: managed_by_salt_formula_sysconfig
    - key_values:
      {%- for k, v in agent.sysconfig.items() %}
        {{ k }}: '{{ v }}'
      {%- endfor %}
    - append_if_not_found: True
    - require:
      - pkg: jenkins_agent_packages

jenkins_agent_service:
  service.running:
    - name: jenkins-agent
    - enable: True
    - watch:
      - suse_sysconfig: jenkins_agent_sysconfig
    - require:
      - pkg: jenkins_agent_packages
{%- else %}
{%- do salt.log.warning('jenkins.agent: no sysconfig defined, skipping configuration') -%}
{%- endif %}
