"""
Helper functions for testing the Juniper Junos formula
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

from jnpr.junos import Device as JunosDevice
import json
import requests

def api(target, path, params={}):
        return requests.get(url=f'https://{target}/rpc/{path}', params=params, verify=False, auth=requests.auth.HTTPBasicAuth('vrnetlab', 'VR-netlab9')).json()

def junos_device(target):
    return JunosDevice(host=target, user='vrnetlab', password='VR-netlab9')

def salt(host, device, command):
    # use custom salt cli to skip deprecation warnings ...
    result = host.run(f'/usr/local/bin/salt --out json {device} {command}')
    output = json.loads(result.stdout)[device]
    return output, result.stderr, result.rc

def salt_apply(host, device, state, test=False):
    return salt(host, device, f'state.apply {state} test={test}')
