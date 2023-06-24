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

from netapp_ontap.resources import Igroup, Lun, LunMap, Svm

log = logging.getLogger(__name__)

def _config():
    return __utils__['ontap_config.config']()

def __virtual__():
    try:
        from netapp_ontap import config as netapp_config 
        from netapp_ontap import NetAppRestError, HostConnection
    except ImportError as err:
        return (False, 'The netapp_ontap library is not available')

    config = _config()
    config_host = config['host']
    verify = config.get('verify', False)
    host, colon, port = config_host.rpartition(':')
    netapp_config.CONNECTION = HostConnection(host, port=port, cert=config['certificate'], key=config['key'], verify=verify)
    netapp_config.RAISE_API_ERRORS = False

    return True

def _path(volume, name):
    return f'/vol/{volume}/{name}'

def _result(result):
    log.debug(f'ontap_ansible: parsing result: {result}')

    error = result.is_err
    status = result.http_response.status_code
    data = result.http_response.json()
    if 'error' in data:
        message = data['error']['message']
    else:
        message = result.http_response.text

    res = {}

    if status >= 400 and error:
        __context__["retcode"] = 2
        res = {'result': False, 'message': message}
    if 200 <= status < 300:
        res = {'result': True}

    if res:
        resmap = {'status': status}
        resmap.update(res)
        return resmap

    log.warning('ontap_ansible: dumping unknown result')
    return result

def _strip(resource, inners=[]):
    resource_dict = resource.to_dict()
    del resource_dict['_links']
    for inner in inners:
        del resource_dict[inner]['_links']
    return resource_dict

# Source: https://stackoverflow.com/a/14996816
suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
def _humansize(nbytes):
    i = 0
    while nbytes >= 1024 and i < len(suffixes)-1:
        nbytes /= 1024.
        i += 1
    f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
    return '%s%s' % (f, suffixes[i])

def get_lun(comment=None, path=None, uuid=None, human=True):
    args = [comment, path, uuid]
    argcount = args.count(None)
    if 1 > argcount < 3:
        log.error(f'Only a single filter may be specified')
        raise ValueError('Only a single filter may be specified')
    fields = 'space.size,status.mapped'
    result = []

    def _handle(resource):
        resource.get(fields=fields)
        resource_stripped = _strip(resource)
        if human:
            resource_stripped['space']['size'] = _humansize(resource_stripped['space']['size'])
        result.append(resource_stripped)

    if comment:
        for resource in Lun.get_collection(**{'comment': comment}):
            _handle(resource)
    elif path:
        for resource in Lun.get_collection(**{'name': path}):
            _handle(resource)
    elif uuid:
        resource = Lun(uuid=uuid)
        _handle(resource)
    else:
        for resource in Lun.get_collection():
            _handle(resource)

    return result

def get_next_free(igroup):
    numbers = []
    for resource in LunMap.get_collection(igroup=igroup, fields="logical_unit_number"):
        numbers.append(resource.logical_unit_number)
    return max(numbers)+1

# https://stackoverflow.com/a/60708339
# based on https://stackoverflow.com/a/42865957/2002471
units = {"B": 1, "KB": 2**10, "MB": 2**20, "GB": 2**30, "TB": 2**40}
def _parse_size(size):
    size = size.upper()
    if not re.match(r' ', size):
        size = re.sub(r'([KMGT]?B)', r' \1', size)
    number, unit = [string.strip() for string in size.split()]
    return int(float(number)*units[unit])

def provision_lun(name, size, volume, vserver, comment=None):
    size = _parse_size(size)
    path = _path(volume, name)

    resource = Lun()
    resource.svm = Svm(name=vserver)
    resource.name = path
    resource.os_type = 'linux'
    resource.space = {'size': size}

    if comment is not None:
        resource.comment = comment

    result = resource.post()
    return _result(result)

# to-do: support property updates other than size changes
def update_lun(uuid, size):
    size = _parse_size(size)

    resource = Lun(uuid=uuid)
    resource.space = {'size': size}
    result = resource.patch()
    return _result(result)

def _delete_lun(name=None, volume=None, uuid=None):
    if (name is None or volume is None) and (uuid is None):
        log.error('Specify either name and volume or uuid')
        raise ValueError('Specify either name and volume or uuid')
    if name and volume:
        path = _path(volume, name)
        resources = get_lun(path=path)
        log.debug(f'netapp_ontap: resources to delete: {resources}')
        found = len(resources)
        if found > 1:
            log.error('Refusing to delete multiple resources')
            return({'result': False, 'message': 'Found more than one matching LUN, aborting deletion'})
        if found == 0:
            return({'result': None, 'message': 'Did not find any matching LUN\'s'})
        resource = Lun(uuid=resources[0]['uuid'])
    elif uuid:
        resource = Lun(uuid=uuid)

    result = resource.delete()
    return _result(result)

def delete_lun_name(name, volume):
    return _delete_lun(name, volume)

def delete_lun_uuid(uuid):
    return _delete_lun(uuid=uuid)

def get_lun_mapped(comment=None, lun_result=None):
    if (comment is None) and (lun_result is None):
        log.error('Specify either a comment or existing LUN output')
        raise ValueError('Specify a comment')
    if comment is not None:
        query = get_lun(comment)
    elif lun_result is not None:
        query = lun_result
    resmap = {}
    for lun in query:
        log.debug(f'netapp_ontap: parsing LUN {lun}')
        name = lun.get('name')
        mapped = lun.get('status', {}).get('mapped')
        resmap.update({name: mapped})
    if None in resmap:
        log.error('netapp_ontap: invalid LUN mapping map')
    return resmap

def get_igroup_uuid(igroup):
    resource = Igroup(name=igroup)
    resource.get()
    uuid = resource.uuid
    return uuid

def get_lun_mapping(name, volume, igroup):
    path = _path(volume, name)
    result = []

    igroup_uuid = get_igroup_uuid(igroup)
    luns = get_lun(path=path)
    log.debug(f'netapp_ontap: found luns: {luns}')
    for resource in luns:
        lun_uuid = resource['uuid']
        mapresource = LunMap(**{'igroup.uuid': igroup_uuid, 'lun.uuid': lun_uuid})
        mrs = mapresource.get_collection(fields='logical_unit_number')
        # FIXME get() fails, saying more than one item is found, and get_collection() returns dozens of completely unrelated entries
        # the loop below is a workaround discarding all the bogus entries
        for mr in mrs:
            mr_stripped = _strip(mr, ['igroup', 'lun', 'svm'])
            if mr_stripped['lun']['uuid'] == lun_uuid and mr_stripped['igroup']['uuid'] == igroup_uuid:
                log.debug(f'netapp_ontap: elected {mr_stripped}')
                result.append(mr_stripped)

    return result

def map_lun(name, lunid, volume, vserver, igroup):
    path = _path(volume, name)

    resource = LunMap()
    resource.svm = Svm(name=vserver)
    resource.igroup = Igroup(name=igroup)
    resource.lun = Lun(name=path)
    resource.logical_unit_number = lunid
    result = resource.post()

    return _result(result)

def unmap_lun(name, volume, igroup):
    path = _path(volume, name)
    results = []

    mappings = get_lun_mapping(name, volume, igroup)
    log.debug(f'netapp_ontap: parsing mappings: {mappings}')
    for mapping in mappings:
        igroup_uuid = mapping['igroup']['uuid']
        lun_uuid = mapping['lun']['uuid']
        resource = LunMap(**{'igroup.uuid': igroup_uuid, 'lun.uuid': lun_uuid})
        result = resource.delete()
        results.append(_result(result))

    if len(mappings) == 1:
        return results[0]

    return results
