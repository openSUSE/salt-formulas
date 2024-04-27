"""
State module for managing sysconfig files on openSUSE

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

def header(name, fillup=None, header_pillar=None):
  """
  Ensures a header is present in the given sysconfig file.
  name = name of the sysconfig file
  fillup = name of the fillup template - defaults to the sysconfig file name
  header_pillar = pillar to use as a file header ("managed_by_salt_sysconfig" by default, as defined in _modules/suse_sysconfig)
  """
  if fillup is None:
    fillup = name
  patterns = __salt__['suse_sysconfig.fillup_regex'](fillup, header_pillar)  # noqa F821
  return __states__['file.replace'](  # noqa F821
    name=name,
    bufsize='file',
    count=1,
    ignore_if_missing=__opts__['test'],  # noqa F821
    pattern=patterns['search'],
    repl=patterns['replace'],
  )

def sysconfig(name, key_values, fillup=None, header_pillar=None, unbool=True, upper=True, append_if_not_found=False):
  """
  Manages both the header and the key/value pairs in a sysconfig file.
  name = sysconfig file to manage (relative paths will be appended to /etc/sysconfig/)
  unbool = whether boolean keys should be converted to quoted yes/no strings
  upper = whether keys should be converted to upper case
  All other arguments are passed to the equally named arguments in the suse_sysconfig.header and file.keyvalue functions.
  """
  if not name.startswith('/'):
    name = f'/etc/sysconfig/{name}'
  boolmap = {
    True: '"yes"',
    False: '"no"',
  }
  key_values = {
    key.upper() if upper else key: boolmap[value] if unbool and isinstance(value, bool) else value for key, value in key_values.items()
  }
  returns = {
    'header': __states__['suse_sysconfig.header'](
                name=name,
                fillup=fillup,
                header_pillar=header_pillar,
              ),
    'config': __states__['file.keyvalue'](
                name=name,
                append_if_not_found=append_if_not_found,
                ignore_if_missing=__opts__['test'],
                key_values=key_values,
              ),
  }

  return_keys = returns.keys()

  results = tuple(
    returns[r].get('result') for r in return_keys
  )
  if False in results:
    result = False
  elif None in results:
    result = None
  elif results[0] and results[1]:
    result = True
  else:
    __salt__['log.error']('suse_sysconfig: result merging failed')
    result = False

  comments = [
    returns[r].get('comment') for r in return_keys
  ]
  if comments[0] == 'Changes would have been made' or 'is set to be changed' in comments[1]:
    comment = f'File {name} would be modified'
  elif comments[0] == 'No changes needed to be made' and not comments[1]:
    comment = comments[0]
  elif comments[0] == 'Changes were made' or 'Changed' in comments[1]:
    comment = f'File {name} modified'
  else:
    comment = ' - '.join(comments)

  diffs = [
    returns[r].get('changes', {}).get('diff') for r in return_keys
  ]

  ret = {
    'name': name,
    'changes': {},
    'result': result,
    'comment': comment,
  }

  if diffs[0] is not None:
    ret['changes'].update({'diff_header': diffs[0]})
  if diffs[1] is not None:
    ret['changes'].update({'diff_config': diffs[1]})

  return ret
