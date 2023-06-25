"""
Salt state module for maging ONTAP based NetApp storage systems
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

def lun_present(name, comment, size, volume, vserver):
    path = f'/vol/{volume}/{name}'
    ret = {'name': path, 'result': False, 'changes': {}, 'comment': ''}

    def _size(details, human=False):
        size = details.get('space', {}).get('size')
        if size is not None and human:
            return _humansize(size)
        return size

    luns = __salt__['ontap.get_lun']()

    for lun in luns:
        lun_path = lun.get('name')
        lun_comment = lun.get('comment')
        lun_uuid = lun.get('uuid')
        if lun_path == path:
            log.debug(f'netapp_ontap: found existing LUN {name}')
            if lun_uuid is None:
                log.error(f'netapp_ontap: found LUN with no UUID')
            lun_details = __salt__['ontap.get_lun'](uuid=lun_uuid, human=False)
            lun_size = _size(lun_details[0], True)
            # lun_size_human = needed?
            if lun_size == size:
                comment_size = f'Size {size} matches'
                ret['result'] = True
            elif lun_size != size:
                if __opts__['test']:
                    comment_size = f'Would resize LUN to {size}'
                else:
                    __salt__['ontap.update_lun'](lun_uuid, size)
                    lun2_details = __salt__['ontap.get_lun'](uuid=lun_uuid, human=False)
                    lun2_size = _size(lun2_details[0], True)
                    comment_size = f'LUN from {lun_size} to {size}'
                    if lun2_size != lun_size and lun2_size == size:
                        comment_size = f'Sucessfully resized {comment_size}'
                        ret['result'] = True
                    elif lun2_size == lun_size:
                        comment_size = f'Failed to resize {comment_size}, it is still {lun2_size}'
                    else:
                        comment_size = f'Unexpected outcome while resizing {comment_size}'

            comment_base = 'LUN is already present'
            retcomment = f'{comment_base}; {comment_size}'
            if __opts__['test']:
                ret['result'] = None
            ret['comment'] = retcomment
            return ret

    if __opts__['test']:
        ret['comment'] = 'Would provision LUN'
        ret['result'] = None
        return ret

    __salt__['ontap.provision_lun'](name, size, volume, vserver, comment)
    lun2_details = __salt__['ontap.get_lun'](path=path)[0]
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

    ret['comment'] = comment
    return ret

def lun_mapped(name, lunid, volume, vserver, igroup):
    path = f'/vol/{volume}/{name}'
    ret = {'name': path, 'result': False, 'changes': {}, 'comment': ''}

    mapping_out = __salt__['ontap.get_lun_mapping'](name, volume, igroup)
    log.debug(f'netapp_ontap: mapping result: {mapping_out}')

    comment_details = f' to igroup {igroup} in SVM {vserver}'
    current_igroup = mapping_out.get('igroup', {}).get('name')
    current_vserver = mapping_out.get('svm', {}).get('name')
    if not mapping_out or igroup != current_igroup or vserver != current_vserver:
        if __opts__['test']:
            comment = f'Would map ID {lunid}{comment_details}'
    elif mapping_out and igroup == current_igroup or vserver == current_svm:
        comment = f'Already mapped{comment_details}'
        ret['result'] = True
    else:
        log.error('Unhandled mapping state')
        comment = 'Something weird happened'

    if __opts__['test'] or ret['result'] is True:
        if __opts__['test']:
            ret['result'] = None
        ret['comment'] = comment
        return ret

    map_out = __salt__['ontap.map_lun'](name, lunid, volume, vserver, igroup)
    if map_out.get('result', False) and map_out.get('status') == 201:
        comment = f'Mapped LUN to ID {lunid} in igroup {igroup}'
        ret['result'] = True
    else:
        comment = 'LUN mapping failed'
        ret['result'] = False

    ret['comment'] = comment
    return ret

def lun_unmapped(name, volume, igroup):
    path = f'/vol/{volume}/{name}'
    ret = {'name': path, 'result': True, 'changes': {}, 'comment': ''}

    if __opts__['test']:
        result = __salt__['ontap.get_lun_mapping'](name, volume, igroup)
        ret['result'] = None
    else:
        result = __salt__['ontap.unmap_lun'](name, volume, igroup)
        rr = result.get('result', True)
        rs = result.get('status')
    log.debug(f'result: {result}')

    if __opts__['test'] and result:
        comment = f'Would unmap LUN'
    elif not result:
        comment = 'Nothing to unmap'
    elif rr is True and rs == 200:
        comment = f'Unmapped LUN'
    elif rr is False or rs != 200:
        comment = f'Unmapping failed'
        ret['result'] = False

    ret['comment'] = comment
    return ret
