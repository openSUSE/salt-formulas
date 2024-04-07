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
