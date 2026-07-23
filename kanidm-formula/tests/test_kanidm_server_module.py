"""
Copyright (C) 2025-2026 Georg Pfuetzenreuter <mail+opensuse@georg-pfuetzenreuter.net>

This program is free software: you can redminetribute it and/or modify
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

from utils import salt
import pytest

@pytest.mark.parametrize(
        'name, success', [
            ('idm_admin', True),
            ('boobaz', False),
        ],
)
def test_kanidm_server_recover_account(host, name, success):
    out, err, rc = salt(host, f'kanidm_server.recover_account {name}')
    if success:
        assert rc == 0
        assert len(out) == 48
    else:
        # TODO (comment in module)
        #assert rc > 0
        assert rc == 0
        assert out is False
