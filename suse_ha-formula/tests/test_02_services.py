import pytest

@pytest.mark.parametrize("service, service_enabled", [('corosync', False), ('pacemaker', True)])
def test_service(host, service, service_enabled):
    unit = host.service(service)
    running = unit.is_running
    enabled = unit.is_enabled
    assert running
    assert enabled is service_enabled
