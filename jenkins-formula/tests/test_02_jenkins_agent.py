"""
Test suite for assessing the Jenkins Agent configuration results
Copyright (C) 2023 Georg Pfuetzenreuter <georg.pfuetzenreuter@suse.com>

This program is free software: you can jenkinstribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

sysconffile = '/etc/sysconfig/jenkins-agent'

def test_jenkins_agent_package(host):
    assert host.package('jenkins-agent').is_installed

def test_jenkins_agent_sysconfig(host):
    with host.sudo():
        assert host.file(sysconffile).contains('^JENKINS_BASE="https://example.com"$')

def test_jenkins_agent_service(host):
    assert host.service('jenkins-agent').is_enabled
