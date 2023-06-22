"""
Salt execution module for maging ONTAP based NetApp storage systems using Ansible
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

import logging

log = logging.getLogger(__name__)

# https://stackoverflow.com/a/9808122
def _find(key, value):
  for k, v in value.items():
    if k == key:
      yield v
    elif isinstance(v, dict):
      for result in find(key, v):
        yield result
    elif isinstance(v, list):
      for d in v:
        for result in find(key, d):
          yield result

def _config():
    return __utils__['ontap_config.config']()

def _call(host, certificate, key, rundir, playbook, extravars={}, descend=[]):
    host, colon, port = host.rpartition(':')
    varmap = {'ontap_host': host, 'ontap_port': int(port), 'ontap_crt': certificate, 'ontap_key': key}
    if extravars:
        varmap.update(extravars)
    log.debug(f'ontap_ansible: executing {playbook} with {varmap} in {rundir}')
    out = __salt__['ansible.playbooks'](
            playbook=playbook, rundir=rundir, extra_vars=varmap)

    plays = out.get('plays', [])
    plays_len = len(plays)
    if not plays_len:
        log.error(f'ontap_ansible: returned with no plays')
        return False
    if plays_len > 0:
        log.warning(f'ontap_ansible: discarding {plays_len} additional plays')
    play0 = plays[0]

    tasks = play0.get('tasks', [])
    tasks_len = len(tasks)
    if not tasks_len:
        log.error(f'ontap_ansible: play returned with no tasks')
        return False
    if tasks_len > 0:
        log.warning(f'ontap_ansible: discarding {tasks_len} additional tasks')
    task0 = tasks[0]

    task = task0.get('hosts').get('localhost')
    if task is None:
        log.error(f'ontap_ansible: unable to parse task - ensure it executed locally')
        return False

    if descend:
        if isinstance(descend, str):
            descend = [descend]
        for level in descend:
            gain = task.get(level)
            if gain is None:
                break
            if gain is not None:
                log.debug(f'ontap_ansible: found artifact for {level}')
                task = gain

    return task


def get_lun(comment=None, uuid=None):
    if (comment is not None) and (uuid is not None):
        log.error(f'Only a single filter may be specified')
        raise ValueError('Only a single filter may be specified')
    varmap = _config()
    extravars = None

    if comment:
        playbook = 'fetch-lun-by-comment_restit'
        extravars = {'extravars': {'ontap_lun_comment': comment}}
    elif uuid:
        playbook = 'fetch-lun_restit'
        extravars = {'extravars': {'ontap_lun_uuid': uuid}}

    if extravars is None:
        playbook = 'fetch-luns_restit'
    else:
        varmap.update(extravars)

    descend = ['response', 'records']
    varmap.update({'playbook': f'playbooks/{playbook}.yml', 'descend': descend})

    result = _call(**varmap)
    return result
