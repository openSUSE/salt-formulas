#!py
"""
Salt state file for applying virtual machine disk images
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

import os
import yaml

def run():
  config = {}
  mypillar = __pillar__['delegated_orchestra']
  target_host = mypillar['deployhost']
  target_part = 'root'
  image = mypillar['image']
  # to-do: set using pillar / default map
  imagepath = '/kvm/images/'
  imagefile = imagepath + mypillar['image']
  if image is None:
    __salt__['log.info']('No disk image specified')
    return config
  # to-do: set using pillar / default map
  mpathmap_file = '/etc/mpathmap'
  with open(mpathmap_file, 'r') as mpathmap_fh:
    mpathmap = yaml.safe_load(mpathmap_fh)
  try:
    mpathid = mpathmap[target_host][target_part]
  except KeyError:
    __salt__['log.error']('Could not determine multipath device')
  mpathdev = '/dev/disk/by-id/dm-uuid-mpath-' + mpathid
  partquery = 'partx -rgoNR ' + mpathdev
  partquery_retcode = __salt__['cmd.retcode'](partquery)
  if partquery_retcode == 0:
    # to-do: allow override using some sort of "force" argument
    __salt__['log.debug']('Existing partitions found - skipping image copy.')
    state = {'test.show_notification': [
                {'text': 'Existing partitions found on {} - skipping image copy'.format(mpathdev)}
            ]
    }
  elif partquery_retcode == 1:
    __salt__['log.debug']('No existing partitions found - writing disk image.')
    # to-do: allow block size override
    state = {'cmd.run': [
                {'name': 'dd if={} of={} bs={}'.format(imagefile, mpathdev, '16M')}
            ]
    }
  config['write_image'] = state
  return config
