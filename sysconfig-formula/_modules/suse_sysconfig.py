"""
Execution module helping with managing sysconfig files on openSUSE

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

from salt.modules.file import file_exists, seek_read


def fillup_regex(fillup, header_pillar=None, pattern_type=None):
  """
  This returns regular expressions for finding and replacing headers in fillup/sysconfig
  files.
  fillup = name of the fillup template
  header_pillar = pillar to use as a file header ("managed_by_salt_sysconfig" by default)
  pattern_type = limit return to only one of the patterns
  """
  if pattern_type not in [None, 'replace', 'search']:
    __salt__['log.error']('os_file: unknown pattern_type')  # noqa F821
    return None
  if header_pillar is None:
    # not set using default arguments to allow for easier handling in state modules
    header_pillar = 'managed_by_salt_sysconfig'
  sysconfig_directory = '/etc/sysconfig/'
  if fillup.startswith(sysconfig_directory):
    fillup = fillup.replace(sysconfig_directory, '')
  fillup_template = f'/usr/share/fillup-templates/sysconfig.{fillup}'
  if file_exists(fillup_template):
    fillup_header = seek_read(fillup_template, 100, 0).decode().split('\n')[0] + '\n'
  else:
    fillup_header = ''
  salt_header = __pillar__.get(header_pillar, '# Managed by Salt')  # noqa F821
  if not salt_header.endswith('\n'):
    salt_header = salt_header + '\n'
  patterns = {
    'replace': fillup_header + salt_header,
    'search': '^' + fillup_header + '(?:' + salt_header + ')?',
  }
  if pattern_type == 'replace':
    return patterns['replace']
  elif pattern_type == 'search':
    return patterns['replace']
  return patterns
