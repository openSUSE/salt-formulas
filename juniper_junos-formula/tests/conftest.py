"""
Pytest helper functions for testing the Juniper Junos formula
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
"""

from jnpr.junos.utils.config import Config as JunosConfig
from lib import junos_device
import pytest

def pytest_addoption(parser):
    parser.addoption('--model', action='store')
    parser.addoption('--target', action='store')

def pytest_generate_tests(metafunc):
    value = metafunc.config.option.target
    if 'target' in metafunc.fixturenames and value is not None:
        metafunc.parametrize('target', [value])

@pytest.fixture
def model(request):
    modelarg = request.config.getoption('--model')
    if modelarg in ['srx', 'vsrx']:
        return 'vsrx-device1'
    if modelarg in ['qfx', 'vqfx']:
        return 'vqfx-device1'

@pytest.fixture
def device(target, model):
    with junos_device(target) as jdevice:
        jconfig = JunosConfig(jdevice, mode='exclusive')
        rescue = jconfig.rescue(action='get')
        if rescue is None:
            jconfig.rescue(action='save')
        else:
            print('Existing rescue configuration, test suite may not behave correctly')

    yield model

    with junos_device(target) as jdevice:
        jconfig = JunosConfig(jdevice, mode='exclusive')
        jconfig.rescue(action='reload')
        jconfig.commit()
        jconfig.rescue(action='delete')

@pytest.fixture
def vlan(target):
    with junos_device(target) as jdevice:
        with JunosConfig(jdevice, mode='exclusive') as jconfig:
            for cmdset in [
                    'set vlans pytest-vlan vlan-id 99',
                    'set vlans pytest-vlan description "VLAN fixture"'
                    ]:
                jconfig.load(cmdset)
            jconfig.commit()

            yield

            jconfig.rollback(1)
            jconfig.commit()
