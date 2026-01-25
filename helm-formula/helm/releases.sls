#!py
"""
Salt states for managing Helm releases
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

from logging import getLogger

log = getLogger(__name__)

def run():
    states = {}
    want_releases = __salt__['pillar.get']('helm:releases', {})

    if not want_releases:
        return states

    have_releases = __salt__['helm.list_releases'](all=True, all_namespaces=True)

    for have in have_releases:
        have_release = have['name']
        have_namespace = have['namespace']

        # filter out system charts managed by RKE2 (TODO: allow filtering already in list_releases() to reduce shell calls?)
        if have_namespace == 'kube-system' and have_release.startswith('rke2-'):
            continue

        for namespace, releases in want_releases.items():
            if have_namespace == namespace and have_release in releases:
                break

        else:
            log.debug(f'Marking release "{have_release}" in namespace "{have_namespace}" for removal.')
            states[f'helm-release-absent-{have_namespace}-{have_release}'] = {
                    'helm.release_absent': [
                        {'name': have_release},
                        {'namespace': have_namespace},
                        {'require': [
                            {'pkg': 'helm-packages'},
                        ]},
                    ],
            }

    for namespace, releases in want_releases.items():
        for release, release_config in releases.items():
            states[f'helm-release-present-{namespace}-{release}'] = {
                    'helm.release_present': [
                        {'name': release},
                        {'namespace': namespace},
                        {'chart': release_config['chart']},
                        {'values': release_config.get('values')},
                        {'description': release_config.get('description')},
                        {'timeout': release_config.get('timeout', '15s')},
                        {'require': [
                            {'pkg': 'helm-packages'},
                        ]},
                    ],
            }

    return states
