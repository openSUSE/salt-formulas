import pytest
import xml.etree.ElementTree as et

@pytest.fixture
def crm_status(host):
    cmd = host.run('crm status xml')
    xml = et.ElementTree(et.fromstring(cmd.stdout)).getroot()
    return xml

def test_socket(host):
    socket = host.socket('udp://239.0.0.1:5405')
    listening = socket.is_listening
    assert listening

@pytest.mark.parametrize('cmd, out', [('crm_node -q', '1\n'), ('crm_node -l | wc -l', '2\n')])
def test_quorum(host, cmd, out):
    cmd = host.run(cmd)
    assert cmd.stdout == out

def test_nodes(crm_status):
    for nodes in crm_status.iter('nodes'):
        for node in nodes.iter('node'):
            attributes = node.attrib
            assert attributes['online'] == 'true'
            assert attributes['standby'] == 'false'
            assert attributes['pending'] == 'false'
            assert attributes['unclean'] == 'false'
            assert attributes['shutdown'] == 'false'







