"""
Helpers for testing of the Helm formula
Copyright (C) 2026 SUSE LLC <georg.pfuetzenreuter@suse.com>

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
"""

import pytest


@pytest.fixture
def clean(host):
    yield

    host.run('sudo salt-call --local helm.uninstall_release exporter1 namespace=formula-test')

@pytest.fixture
def populated(host):
    host.run('sudo salt-call --local helm.install_or_upgrade_release release_name=exporter1 chart=oci://ghcr.io/prometheus-community/charts/prometheus-blackbox-exporter namespace=formula-test values=\"{"replicas": 2}\"')

    yield

    host.run('sudo salt-call --local helm.uninstall_release exporter1 namespace=formula-test')
    host.run('sudo salt-call --local helm.uninstall_release exporter2 namespace=formula-test')
