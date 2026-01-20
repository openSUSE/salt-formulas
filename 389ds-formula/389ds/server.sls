#!py
"""
vim: ft=python.salt

Salt states for managing 389-DS instances
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

def _run_manage_instance(name, config):
    _states = {}
    _id = f'389ds-{name}'

    log.debug(f'Managing instance "{name}" with config "{config}".')

    answers = {
            'general': {
                'config_version': 2,
                'start': False,
            },
            'slapd': {
                'instance_name': name,
            },
    }

    for section, options in config.get('config', {}).items():
        if section == 'general' or ( section not in answers and section[0:8] != 'backend-' ) or not isinstance(options, dict):
            log.warn(f'389ds: unhandled answer section "{section}", skipping')
            continue

        if section not in answers:
            answers[section] = {}

        for k, v in options.items():
            # some options take real booleans, others don't
            if k == 'sample_entries':
                if v is True:
                    v = 'yes'
                elif v is False:
                    v = 'no'

            answers[section][k] = v

    # TODO: better path handling
    answer_file = f'/root/.389_{name}.inf'

    _states[f'{_id}-answer-file'] = {
            'file.serialize': [
                {'name': answer_file},
                {'serializer': 'configparser'},
                {'dataset': answers},
                {'mode': '0600'},
                {'user': 'root'},
                {'group': 'root'},
            ],
    }

    _states[f'{_id}-create'] = {
            'cmd.run': [
                {'name': f'dscreate -j from-file {answer_file}'},
                {'unless': f'dsctl -l | grep -q ^slapd-{name}$'},
                {'shell': '/bin/sh'},
                {'require': [
                    {'pkg': '389ds-packages'},
                ]},
            ],
    }

    _states[f'{_id}-start'] = {
            'service.running': [
                {'name': f'dirsrv@{name}'},
                {'enable': True},
                {'require': [
                    {'pkg': '389ds-packages'},
                    {'cmd': f'{_id}-create'},
                ]},
            ],
    }

    for suffix, replconfig in config.get('replication', {}).items():
        _states[f'{_id}-replication-{suffix}'] = {
                '389ds.manage_replication': [
                    {'instance': name},
                    {'suffix': suffix},
                    {'role': replconfig.get('role')},
                    {'replica_id': replconfig.get('replica-id')},
                    {'bind_dn': replconfig.get('bind-dn')},
                    {'bind_passwd': replconfig.get('bind-passwd')},
                    {'require': [
                        {'pkg': '389ds-packages'},
                        {'cmd': f'{_id}-create'},
                    ]},
                ],
        }

    return _states


def run():
    states = {}

    states['389ds-packages'] = {
            'pkg.installed': [
                {'pkgs': ['389-ds']},
                {'reload_modules': True},  # to make lib389 available
            ],
    }

    for name, config in __salt__['pillar.get']('389ds:instances', {}).items():
        states.update(_run_manage_instance(name, config))

    return states
