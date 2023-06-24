"""
Salt state module for managing LUNs using the ONTAP Ansible collection
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

# Source: https://stackoverflow.com/a/14996816
suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
def _humansize(nbytes):
    i = 0
    while nbytes >= 1024 and i < len(suffixes)-1:
        nbytes /= 1024.
        i += 1
    f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
    return '%s%s' % (f, suffixes[i])

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

def lun_present(name, comment, size, volume, vserver, lunid=None, igroup=None):
    path = f'/vol/{volume}/{name}'
    ret = {'name': path, 'result': False, 'changes': {}, 'comment': ''}
    size_ok = False
    map_ok = False
    if not None in [lunid, igroup]:
        do_map = True
    else:
        do_map = False

    def _size(details, human=False):
        size = details.get('space', {}).get('size')
        if size is not None and human:
            return _humansize(size)
        return size

    # FIXME drop mapping logic from lun_present in favor of lun_mapped
    def _map(name, lunid, volume, vserver, igroup):
        ok = False
        map_out = __salt__['ontap_native.map_lun'](name, lunid, volume, vserver, igroup)
        if map_out.get('result', False) and map_out.get('status') == 201:
            comment = f'Mapped LUN to ID {lunid}'
            ok = True
            # consider another get_lun to validate .. given the queries being expensive in time, it should be combined with the resize validation
        else:
            comment = 'LUN mapping failed'
        return comment, ok

    query = __salt__['ontap_native.get_lun']()
    #luns = query[0]
    luns = query
    next_free = __salt__['ontap_native.get_next_free']('wilde') # drop this

    for lun in luns:
        lun_path = lun.get('name')
        lun_comment = lun.get('comment')
        lun_uuid = lun.get('uuid')
        if lun_comment == comment or lun_path == path:
            log.debug(f'netapp_ontap: found existing LUN {name}')
            if lun_uuid is None:
                log.error(f'netapp_ontap: found LUN with no UUID')
            lun_details = __salt__['ontap_native.get_lun'](uuid=lun_uuid, human=False)
            lun_size = _size(lun_details[0], True)
            # lun_size_human = needed?
            lun_mapping = __salt__['ontap_native.get_lun_mapped'](lun_result=lun_details)
            lun_mapped = lun_mapping.get(name)
            # lun_id = needed?
            if lun_size == size:
                comment_size = f'Size {size} matches'
                size_ok = True
            elif lun_size != size:
                if __opts__['test']:
                    comment_size = f'Would resize LUN to {size}'
                else:
                    __salt__['ontap_native.update_lun'](lun_uuid, size)
                    lun2_details = __salt__['ontap_native.get_lun'](uuid=lun_uuid, human=False)
                    lun2_size = _size(lun2_details[0], True)
                    comment_size = f'LUN from {lun_size} to {size}'
                    if lun2_size != lun_size and lun2_size == size:
                        comment_size = f'Sucessfully resized {comment_size}'
                        size_ok = True
                    elif lun2_size == lun_size:
                        comment_size = f'Failed to resize {comment_size}, it is still {lun2_size}'
                    else:
                        comment_size = f'Unexpected outcome while resizing {comment_size}'

            if not do_map:
                comment_mapping = None
                map_ok = True
            else:
                if lun_mapped:
                    comment_mapping = 'Already mapped'
                    map_ok = True
                else:
                    map_out = _map(name, lunid, volume, vserver, igroup)
                    comment_mapping = map_out[0]
                    map_ok = map_out[1]

                    #map_out = __salt__['ontap_native.map_lun'](name, lunid, volume, vserver, igroup)
                    #if map_out.get('result', False) and map_out.get('status') == 201:
                    #    comment_mapping = f'Mapped LUN to ID {lunid}'
                    #    map_ok = True
                    #    # consider another get_lun to validate .. given the queries being expensive in time, it should be combined with the resize validation
                    #else:
                    #    comment_mapping = 'LUN mapping failed'

            comment_base = 'LUN is already present'
            if size_ok and map_ok:
                ret['result'] = True
            retcomment = f'{comment_base}; {comment_size}'
            if comment_mapping is not None:
                retcomment = f'{retcomment}, {comment_mapping}'
            if __opts__['test']:
                ret['result'] = None
            ret['comment'] = retcomment
            return ret

    if __opts__['test']:
        ret['comment'] = 'Would provision LUN'
        ret['result'] = None
        return ret

    __salt__['ontap_native.provision_lun'](name, size, volume, vserver, comment)
    if do_map:
        map_out = _map(name, lunid, volume, vserver, igroup)
        comment_mapping = map_out[0]
        map_ok = map_out[1]
    lun2_details = __salt__['ontap_native.get_lun'](comment)[0]
    lun2_size = _size(lun2_details)
    # FIXME changes dict

    if lun2_details.get('name') == path:
        ret['result'] = True
        comment_path = f'{path} created'
    else:
        ret['result'] = False
        comment_path = f'{path} not properly created'

    if lun2_size == size:
        ret['result'] = True
        comment_size = f'with size {size}'
    else:
        ret['result'] = False
        comment_size = f'with mismatching size {lun2_size}'

    comment = f'LUN {comment_path} {comment_size}.'

    if do_map:
        if map_ok:
            ret['result'] = True
            comment_mapping = f'mapped to ID {lunid}'
        else:
            ret['result'] = False
            comment_mapping = f'mapping to ID {lunid} failed'
        comment = f'{comment} LUN {comment_mapping}.'

    ret['comment'] = comment
    return ret

def lun_mapped(name, lunid, volume, vserver, igroup):
    path = f'/vol/{volume}/{name}'
    ret = {'name': path, 'result': False, 'changes': {}, 'comment': ''}

    mapping_out = __salt__['ontap_native.get_lun_mapping'](name, volume, igroup)
    log.debug(f'netapp_ontap: mapping result: {mapping_out}')
    current_igroups = []
    current_svms = []
    records = mapping_out.get('num_records')
    do_igroup = True
    do_svm = True
    do_map = False
    if records == 0:
        do_map = True
        if __opts__['test']:
            comment = 'Would create mapping'
    elif records is not None and records > 0:
        for mapping in mapping_out.get('records', []):
            this_igroup = mapping.get('igroup', {}).get('name')
            if this_igroup is None:
                log.error(f'netapp_ontap: unable to determine igroup in mapping result')
            else:
                if this_igroup not in current_igroups:
                    current_igroups.append(this_igroup)
            this_svm = mapping.get('svm', {}).get('name')
            if this_svm is None:
                log.error(f'netapp_ontap: unable to determine svm in mapping result')
            else:
                if this_svm not in current_svms:
                    current_svms.append(this_svm)

    comment_igroup = f' to igroup {igroup}'
    if igroup in current_igroups:
        do_igroup = False

    comment_svm = f' in SVM {vserver}'
    if vserver in current_svms:
        do_svm = False

    comments = f'{comment_igroup}{comment_svm}'
    already = False
    if do_map or do_igroup or do_svm:
        if __opts__['test']:
            comment = f'Would map ID {lunid}{comments}'
    elif not do_igroup or not do_svm:
        comment = f'Already mapped{comment_igroup}{comment_svm}'
        ret['result'] = True
    else:
        log.error('Unhandled mapping state')
        comment = 'Something weird happened'

    if __opts__['test']:
        ret['result'] = None
    if __opts__['test'] or ret['result'] is True:
        ret['comment'] = comment
        return ret

    map_out = __salt__['ontap_native.map_lun'](name, lunid, volume, vserver, igroup)
    if map_out.get('result', False) and map_out.get('status') == 201:
        comment = f'Mapped LUN to ID {lunid} in igroup {igroup}'
        ret['result'] = True
    else:
        comment = 'LUN mapping failed'
        ret['result'] = False

    ret['comment'] = comment
    return ret

