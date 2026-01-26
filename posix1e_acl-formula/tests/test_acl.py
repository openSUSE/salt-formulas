"""
Test suite for assessing the posix1e_acl formula functionality
Copyright (C) 2024 Georg Pfuetzenreuter <mail+opensuse@georg-pfuetzenreuter.net>

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

from pytest import mark

@mark.parametrize(
  'pillar', [
    ({'/tmp/posix1e_formula_acl_test1': {'user': {'georg': {'read': True}}}}),
    ({'/tmp/posix1e_formula_acl_test2': {'group': {'georg': {'read': True, 'write': True}}}}),
    ({'/tmp/posix1e_formula_acl_test3': {'user': {'georg': {'read': True}}, 'group': {'georg': {'read': True, 'write': True}}}}),
  ],
  indirect=['pillar']
)
@mark.parametrize('test', [True, False])
def test_acl(host, pillar, salt_apply, test):
  result = salt_apply

  assert len(result) > 0
  assert result[2] == 0

  output = result[0]
  state_pkg = 'pkg_|-posix1e_packages_|-posix1e_packages_|-installed'

  assert state_pkg in output
  assert output[state_pkg].get('result') is True

  file = list(pillar['acl'].keys())[0]
  acl_types = list(pillar['acl'][file].keys())

  for acl_type in acl_types:

    acl_names = list(pillar['acl'][file][acl_type].keys())
    for acl_name in acl_names:
      state_acl_name = f'{file}_{acl_type}_{acl_name}'
      state_acl = f'posix1e_acl_|-posix1e_acls_|-{state_acl_name}_|-present'
      state_acl_out = output[state_acl]

      assert state_acl_out.get('name') == state_acl_name

      expected = {}
      expected['changes'] = {'new': pillar['acl'][file][acl_type][acl_name]}

      for permission in ['read', 'write', 'execute']:
        if permission not in expected['changes']['new']:
          expected['changes']['new'][permission] = False

      if test:
        expected['result'] = None
        expected['comment'] = f'Would have changed ACL for {acl_type} "{acl_name}" on {file}.'

      else:
        expected['result'] = True
        expected['comment'] = f'Changed ACL for {acl_type} "{acl_name}" on {file}.'

      for return_key, return_value in expected.items():
        assert state_acl_out.get(return_key) == return_value
