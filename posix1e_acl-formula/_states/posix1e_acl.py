"""
State module for managing POSIX.1e style ACLs

Copyright (C) 2024 Georg Pfuetzenreuter <mail+opensuse@georg-pfuetzenreuter.net>

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

from salt import exceptions

def present(name, acl_type, acl_name, permissions={}, path=None):
  ret = {'name': name, 'result': False, 'changes': {'old': {}, 'new': {}}, 'comment': ''}
  is_test = __opts__['test']

  if path is not None:
    name = path

  valid_types = ['user', 'group']
  if acl_type not in valid_types:
    raise exceptions.SaltInvocationError(f'Argument "acl_type" must be one of {valid_types}.')
  
  if not isinstance(permissions, dict):
    raise exceptions.SaltInvocationError('Argument "perms" must be a dictionary.')

  for p in ['read', 'write', 'execute']:
    if p not in permissions:
      permissions.update({p: False})

  have_aclmap = __salt__['posix1e_acl.getfacl'](name).get(acl_type, {})
  changes = ret['changes']

  found_changes = False

  if acl_name in have_aclmap:
    have_aclmap = have_aclmap.get(acl_name, {})

    for permission, value_have in have_aclmap.items():
      value_want = permissions[permission]
      if value_have != value_want:
        found_changes = True
        changes['new'].update({permission: value_want})
        changes['old'].update({permission: value_have})

  else:
    found_changes = True

  msg = f'for {acl_type} "{acl_name}" on {name}'

  if found_changes and not ( changes['new'] and changes['old'] ):
    changes['new'] = permissions
    del changes['old']

    #if is_test:
    #  ret['comment'] = f'Would have created ACL {msg}.'
    #  ret['result'] = None

    #  return ret

  if not found_changes:
    del changes['new']
    del changes['old']

  if not changes:
    ret['comment'] = f'ACL {msg} is already in the right state.'
    ret['result'] = True

    return ret

  if changes and is_test:
    ret['comment'] = f'Would have changed ACL {msg}.'
    ret['result'] = None

    return ret

  ret['result'] = __salt__['posix1e_acl.setfacl'](name, {'target_name': acl_name, 'target_type': acl_type, **permissions})

  if ret['result']:
    ret['comment'] = f'Changed ACL {msg}.'
  else:
    ret['comment'] = f'Failed to change ACL {msg}.'

  return ret
