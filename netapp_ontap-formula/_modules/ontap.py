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
import re

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

def _result(result):
    log.debug(f'ontap_ansible: parsing result: {result}')

    error = result.get('error_message')
    status = result.get('status_code')
    changed = result.get('changed')
    response = result.get('response')
    method = result.get('invocation', {}).get('module_args', {}).get('method')
    if response is not None and 'num_records' in response:
        records = response['num_records']
    elif method == 'POST':
        # API does not return a record number for any creation calls, we cannot tell how many items changed
        records = None
    else:
        # API does not return a record number if a DELETE call did not yield any deletions
        records = 0

    res = {}

    if status >= 400 and error:
        __context__["retcode"] = 2
        res = {'error': error, 'result': False}
    if 200 <= status < 300:
        res = {'result': True}

    if res:
        resmap = {'status': status}
        if records is not None:
            resmap.update({'changed': records})
        resmap.update(res)
        return resmap

    log.warning('ontap_ansible: dumping unknown result')
    return result

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

# https://stackoverflow.com/a/60708339
# based on https://stackoverflow.com/a/42865957/2002471
units = {"B": 1, "KB": 2**10, "MB": 2**20, "GB": 2**30, "TB": 2**40}
def _parse_size(size):
    size = size.upper()
    #print("parsing size ", size)
    if not re.match(r' ', size):
        size = re.sub(r'([KMGT]?B)', r' \1', size)
    number, unit = [string.strip() for string in size.split()]
    return int(float(number)*units[unit])

def provision_lun(name, size, lunid, volume, vserver):
    varmap = _config()
    size = _parse_size(size)
    varmap.update({'playbook': 'playbooks/deploy-lun_restit.yml', 'extravars': {'ontap_comment': name, 'ontap_lun_id': lunid, 'ontap_volume': volume, 'ontap_vserver': vserver, 'ontap_size': size}})
    result = _call(**varmap)
    return _result(result)

def _delete_lun(name=None, volume=None, uuid=None):
    if (name is None or volume is None) and (uuid is None):
        log.error('Specify either name and volume or uuid')
        raise ValueError('Specify either name and volume or uuid')
    varmap = _config()
    if name and volume:
        extravars = {'ontap_volume': volume, 'ontap_lun_name': name}
    elif uuid:
        extravars = {'ontap_lun_uuid': uuid}
    varmap.update({'playbook': 'playbooks/delete-lun_restit.yml', 'extravars': extravars})
    result = _call(**varmap)
    return _result(result)

def delete_lun_name(name, volume):
    return _delete_lun(name, volume)

def delete_lun_uuid(uuid):
    return _delete_lun(uuid=uuid)

def get_lun_mapping(comment):
    query = get_lun(comment)
    resmap = {}
    for lun in query:
        log.debug(f'netapp_ontap: parsing LUN {lun}')
        name = lun.get('name')
        mapped = lun.get('status', {}).get('mapped')
        resmap.update({name: mapped})
    if None in resmap:
        log.error('netapp_ontap: invalid LUN mapping map')
    return resmap

def _path(volume, name):
    return f'/vol/{volume}/{name}'

def map_lun(name, lunid, volume, vserver, igroup):
    varmap = _config()
    path = _path(volume, name)
    varmap.update({'playbook': 'playbooks/map-lun_restit.yml', 'extravars': {'ontap_lun_id': lunid, 'ontap_lun_path': path, 'ontap_vserver': vserver, 'ontap_igroup': igroup}})
    result = _call(**varmap)
    return _result(result)

def unmap_lun(name, volume, igroup):
    varmap = _config()
    path = _path(volume, name)
    varmap.update({'playbook': 'playbooks/unmap-lun_restit.yml', 'extravars': {'ontap_lun_path': path, 'ontap_igroup': igroup}})
    result = _call(**varmap)
    return _result(result)
