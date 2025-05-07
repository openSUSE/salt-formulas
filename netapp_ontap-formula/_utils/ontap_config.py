"""
Salt utility module for providing functions used by other ONTAP related modules
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

def config():
    config = __pillar__.get('netapp_ontap', {})
    host = config.get('host')
    certificate = config.get('certificate')
    key = config.get('key')
    rundir = config.get('rundir')
    if None in [host, certificate, key, rundir]:
        log.error('netapp_ontap: configuration is incomplete!')
        return False
    return {'host': host, 'certificate': certificate, 'key': key, 'rundir': rundir}
