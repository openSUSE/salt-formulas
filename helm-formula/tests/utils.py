"""
Helpers for testing of the Helm formula
Copyright (C) 2026 SUSE LLC <georg.pfuetzenreuter@suse.com>

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

from json import loads
from shlex import quote


def salt_state_apply(host, pillar, test):
    pillar = quote(str(pillar))
    result = host.run(f'sudo salt-call --local --out json state.apply helm pillar={pillar} test={test}')

    output = loads(result.stdout)['local']

    return output, result.stderr, result.rc
