"""
Salt execution module for fetching LUN information related to virtual machines
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

import re

# to-do: better Ansible output parsing
# to-do: make playbook, lunmap and mpathmap locations configurable

# Source: https://stackoverflow.com/a/7085715
def _get_trailing_number(s):
    m = re.search(r'\d+$', s)
    return int(m.group()) if m else None

def get_lun_by_comment(host, comment):
    ansible_extravar = {'ontap_host': host, 'ontap_lun_comment': comment}
    lun_out = __salt__['ansible.playbooks'](playbook='playbooks/fetch-lun-by-comment.yml', rundir='/srv/ansible', extra_vars=ansible_extravar)
    lun_details = lun_out['plays'][0]['tasks'][0]['hosts']['localhost']['ontap_info']['storage/luns']['records'][0]
    return(lun_details)

def get_lun_id(host, comment):
    lun_details = get_lun_by_comment(host, comment)
    lun_id = _get_trailing_number(lun_details['name'])
    return(lun_id)

def get_lun_map():
    import csv
    mydict = {}
    with open('/etc/lunmap', mode='r') as infile:
        csv_reader = csv.reader(infile, delimiter=',')
        for row in csv_reader:
            if len(row) == 0 or row[0].startswith('#'):
                continue
            mydict.update({row[0]: row[1]})
    return(mydict)

def get_mpath_map():
    import yaml
    with open('/etc/mpathmap', mode='r') as infile:
        myyaml = yaml.safe_load(infile)
    return(myyaml)
