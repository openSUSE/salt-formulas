"""
Pytest helper functions for testing the Juniper Junos formula
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
"""

import pytest

def pytest_addoption(parser):
    parser.addoption('--target', action='store')

def pytest_generate_tests(metafunc):
    value = metafunc.config.option.target
    if 'target' in metafunc.fixturenames and value is not None:
        metafunc.parametrize('target', [value])

@pytest.fixture
def device():
    return 'vsrx-device1'
