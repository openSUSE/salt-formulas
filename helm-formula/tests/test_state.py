"""
Test suite for Salt states in the Helm formula
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

from copy import deepcopy

import pytest
from utils import salt_state_apply

PILLAR = {'helm': {
            'releases': {
                'formula-test': {
                    'exporter1': {
                        'chart': {
                            'name': 'oci://ghcr.io/prometheus-community/charts/prometheus-blackbox-exporter',
                            'version': '11.7.0',
                        },
                        'values': {
                            'replicas': 2,
                        },
                    },
                },
            },
        },
}

STATES = [
    'pkg_|-helm-packages_|-helm-packages_|-installed',
    'helm_|-helm-release-present-formula-test-exporter1_|-exporter1_|-release_present',
]


@pytest.mark.parametrize('test', [True, False])
def test_release_new(host, test, clean):
    out, err, rc = salt_state_apply(host, PILLAR, test)

    assert rc == 0

    for state in STATES:
        assert state in out

    assert len(out) == len(STATES)

    low = out[STATES[1]]

    if test:
        assert low['result'] is None
        assert low['comment'] == 'Would install release.'

    else:
        assert low['result'] is True
        assert low['comment'] == 'Successfully installed release.'


@pytest.mark.parametrize('test', [True, False])
def test_release_nochanges(host, test, populated):
    out, err, rc = salt_state_apply(host, PILLAR, test)

    assert rc == 0

    for state in STATES:
        assert state in out

    assert len(out) == len(STATES)

    low = out[STATES[1]]

    assert low['result'] is True
    assert low['comment'] == 'Release matches the configuration.'
    assert low['changes'] == {}


@pytest.mark.parametrize('test', [True, False])
def test_release_changes(host, test, populated):
    changed_pillar = deepcopy(PILLAR)
    changed_pillar['helm']['releases']['formula-test']['exporter1']['values']['replicas'] = 1

    out, err, rc = salt_state_apply(host, changed_pillar, test)

    assert rc == 0

    for state in STATES:
        assert state in out

    assert len(out) == len(STATES)

    low = out[STATES[1]]

    if test:
        assert low['result'] is None
        assert low['comment'] == 'Would update release.'
        assert low['changes'] == {
                'new': {
                    'values': {
                        'replicas': 1,
                    },
                },
                'old': {
                    'values': {
                        'replicas': 2,
                    },
                },
        }

    else:
        assert low['result'] is True
        assert low['comment'] == 'Successfully updated release.'
        assert low['changes'] == {
                'new': {
                    'chart': {
                        'name': 'prometheus-blackbox-exporter',
                        'version': '11.7.0',
                    },
                    'name': 'exporter1',
                    'namespace': 'formula-test',
                    'status': 'deployed',
                    'values': {
                        'replicas': 1,
                    },
                },
                'old': {
                    'values': {
                        'replicas': 2,
                    },
                },
        }


@pytest.mark.parametrize('test', [True, False])
def test_release_cleanup(host, test, populated):
    changed_pillar = {'helm': {'releases': {
        'formula-test': {
            'exporter2': {
                'chart': {
                    'name': 'oci://ghcr.io/prometheus-community/charts/prometheus-blackbox-exporter',
                    'version': '11.7.0',
                },
            },
        },
    }}}

    state_absent = 'helm_|-helm-release-absent-formula-test-exporter1_|-exporter1_|-release_absent'
    state_present = 'helm_|-helm-release-present-formula-test-exporter2_|-exporter2_|-release_present'

    out, err, rc = salt_state_apply(host, changed_pillar, test)

    assert rc == 0

    assert len(out) == 3

    got_states = list(out.keys())

    assert got_states[1] == state_absent
    assert got_states[2] == state_present

    low = out[state_absent]

    assert low['name'] == 'exporter1'

    if test:
        assert low['result'] is None
        assert low['comment'] == 'Would uninstall release.'

    else:
        assert low['result'] is True
        assert low['comment'] == 'Successfully uninstalled release.'

    assert low['changes'] == {
            'old': {
                'name': 'exporter1',
            },
            'new': {
                'name': None,
            },
    }
