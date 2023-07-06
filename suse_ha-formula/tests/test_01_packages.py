import pytest

@pytest.mark.parametrize('package', ['corosync', 'pacemaker', 'crmsh', 'resource-agents'])
def test_packages(host, package):
    installed = host.package(package).is_installed
    assert installed
