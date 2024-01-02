"""
Salt state module for managing LUNs using the ONTAP Ansible collection
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

import logging
import re

log = logging.getLogger(__name__)

# to-do: some of these function should go into an execution module ...
# to-do: make playbook/rundir configurable
# to-do: parse unexpected results better
# to-do: handle test=True

def _query_luns(host):
    ansible_extravar = {'ontap_host': host}
    lun_out = __salt__['ansible.playbooks'](playbook='playbooks/fetch-luns.yml', rundir='/srv/ansible', extra_vars=ansible_extravar)
    all_luns = lun_out['plays'][0]['tasks'][0]['hosts']['localhost']['ontap_info']['storage/luns']
    next_free_lun = lun_out['plays'][0]['tasks'][3]['hosts']['localhost']['ansible_facts']['lun_id']
    return(all_luns, next_free_lun)

def _query_lun(host, uuid):
    ansible_extravar = {'ontap_host': host, 'ontap_lun_uuid': uuid}
    lun_out = __salt__['ansible.playbooks'](playbook='playbooks/fetch-lun.yml', rundir='/srv/ansible', extra_vars=ansible_extravar)
    lun_details = lun_out['plays'][0]['tasks'][0]['hosts']['localhost']['ontap_info']['storage/luns']['records'][0]
    return(lun_details)

def _create_lun(name, host, size, lunid, volume, vserver):
    size = size.rstrip('GB')
    ansible_extravar = {'ontap_lun_id': lunid, 'ontap_host': host, 'ontap_size': size, 'ontap_volume': volume, 'ontap_vserver': vserver, 'ontap_comment': name}
    lun_out = __salt__['ansible.playbooks'](playbook='playbooks/deploy-lun.yml', rundir='/srv/ansible', extra_vars=ansible_extravar)
    return(lun_out)

def _map_lun(host, lunid, volume, vserver, igroup, cluster):
    ansible_extravar = {'ontap_lun_id': lunid, 'ontap_host': host, 'ontap_volume': volume, 'ontap_vserver': vserver, 'ontap_igroup': igroup}
    map_out = __salt__['ansible.playbooks'](playbook='playbooks/map-lun.yml', rundir='/srv/ansible', extra_vars=ansible_extravar)
    return(map_out)

# Source: https://stackoverflow.com/a/14996816
suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
def humansize(nbytes):
    i = 0
    while nbytes >= 1024 and i < len(suffixes)-1:
        nbytes /= 1024.
        i += 1
    f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
    return '%s%s' % (f, suffixes[i])

# Source: https://stackoverflow.com/a/7085715
def get_trailing_number(s):
    m = re.search(r'\d+$', s)
    return int(m.group()) if m else None

def question_size(name, host, size):
    ret = {'name': name, 'result': False, 'changes': {}, 'comment': ''}
    lun_query = _query_luns(host)
    all_luns = lun_query[0]
    for lun in all_luns['records']:
        if 'comment' in lun:
            if lun['comment'] == name:
                lun_details = _query_lun(host, lun['uuid'])
                lun_size = humansize(lun_details['space']['size'])
                lun_size_human = humansize(lun_details['space']['size'])
                # instead of comparing two human sizes, it might be better to convert the input size to bytes in order to compare exact values
                if size == lun_size_human:
                    ret['result'] = True
                    ret['comment'] = 'Disk for {0} matches size {1}'.format(name, size)
                    return(ret)
                if size != lun_size:
                    ret['result'] = False
                    ret['comment'] = 'Found disk for {0}, but requested size {1} does not match {2}'.format(name, size, lun_size_human)
                    ret['changes'] = lun_details
                    return(ret)
    ret['result'] = False
    ret['comment'] = 'No matching LUN found'
    ret['changes'] = all_luns
    return(ret)

def question_mapping(name, host):
    ret = {'name': name, 'result': False, 'changes': {}, 'comment': ''}
    lun_query = _query_luns(host)
    all_luns = lun_query[0]
    for lun in all_luns['records']:
        if 'comment' in lun:
            if lun['comment'] == name:
                lun_details = _query_lun(host, lun['uuid'])
                lun_mapped = lun_details['status']['mapped']
                if lun_mapped:
                    ret['result'] = True
                    ret['comment'] = 'LUN {0} is mapped'.format(name)
                    return(ret)
                else:
                    ret['comment'] = 'Found LUN {0}, but it is not mapped'.format(name)
                    ret['changes'] = lun_details
                    return(ret)
    ret['comment'] = 'No matching LUN found'
    ret['changes'] = all_luns
    return(ret)

def present(name, host, size, volume, vserver, igroup, cluster):
    ret = {'name': name, 'result': False, 'changes': {}, 'comment': ''}
    lun_query = _query_luns(host)
    all_luns = lun_query[0]
    for lun in all_luns['records']:
        if 'comment' in lun:
            if lun['comment'] == name:
                lun_details = _query_lun(host, lun['uuid'])
                lun_size = lun_details['space']['size']
                lun_size_human = humansize(lun_size)
                lun_mapped = lun_details['status']['mapped']
                lun_id = get_trailing_number(lun_details['name'])
                # instead of comparing two human sizes, it might be better to convert the input size to bytes in order to compare exact values
                comment_base = 'Found existing disk for {0}'.format(name)
                if size == lun_size_human:
                    comment_size = 'Size {0} matches'.format(lun_size_human)
                elif size != lun_size:
                    _create_lun(name, host, size, lun_id, volume, vserver)
                    fetch_call = question_size(name, host, size)
                    ret['changes'] = fetch_call
                    if fetch_call['result']:
                        comment_size =  'Resized from {0} to {1}'.format(lun_size_human, size)
                    else:
                        ret['result'] = False
                        ret['comment'] = 'Disk resize failed!'
                        return(ret)
                if lun_mapped:
                    comment_mapping = 'Already mapped'
                else:
                    _map_lun(host, lun_id, volume, vserver, igroup, cluster)
                    fetch_call = question_mapping(name, host)
                    if fetch_call['result']:
                        comment_mapping = 'Mapped LUN to ID {0}'.format(lun_id)
                    else:
                        ret['result'] = False
                        ret['comment'] = 'LUN mapping failed!'
                        return(ret)
                ret['result'] = True
                ret['comment'] = comment_base + ' - ' + comment_size + ' - ' + comment_mapping
                return(ret)
    lun_id = lun_query[1]
    _create_lun(name, host, size, lun_id, volume, vserver)
    fetch_size_call = question_size(name, host, size)
    ret['changes'] = fetch_size_call
    if fetch_size_call['result']:
        _map_lun(host, lun_id, volume, vserver, igroup, cluster)
        fetch_mapping_call = question_mapping(name, host)
        if fetch_mapping_call['result']:
            ret['result'] = True
            ret['comment'] = 'Disk for {0} with size {1} created and mapped to LUN ID {2}'.format(name, size, lun_id)
        else:
            ret['result'] = False
            ret['comment'] = 'Disk for {0} with size {1} created, but mapping failed'.format(name, size)
    else:
        ret['comment'] = 'Disk creation went horribly wrong.'
    return(ret)

def mpathmap(name, clusterhost, disks, netapphost, vm):
    ret = {'name': name, 'result': False, 'changes': {}, 'comment': ''}
    ansible_extravar = {'cluster_host': clusterhost, 'disks': disks, 'ontap_host': netapphost, 'vm': vm}
    play_out = __salt__['ansible.playbooks'](playbook='playbooks/mpathmap.yml', rundir='/srv/ansible', extra_vars=ansible_extravar)
    tasks = play_out['plays'][0]['tasks']
    changed = None
    # there are probably more efficient ways to do this
    for taskid, task in enumerate(tasks):
        if task['task']['name'] == 'Update block in mpathmap':
            log.debug('Found matching task at position %d' % taskid)
            changes = task['hosts']['localhost']
            changed = changes['changed']
    if changed == None:
        ret['comment'] = 'Failed to generate mpathmap'
    if changed == False:
        ret['comment'] = 'Block in mpathmap for {0} on {1} already in its correct state'.format(vm, clusterhost)
        ret['result'] = True
    if changed == True:
        ret['comment'] = 'Updated mpathmap block for {0} on {1}'.format(vm, clusterhost)
        ret['result'] = changed
    return(ret)
