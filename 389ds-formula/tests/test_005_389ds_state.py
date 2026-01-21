"""
Test suite for Salt states in the 389-DS formula
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

import pytest
from utils import INSTANCE, PASS, SUFFIX, expand_expect_out, reduce_state_out


@pytest.mark.parametrize(
  'pillar, expect', [
    # 0. no 389ds pillar
    (
      {},
      {
          'pkg_|-389ds-packages_|-389ds-packages_|-installed': {
              'name': '389ds-packages',
              'result': (None, True),
          },
      },
    ),

    # 1. pillar with only config
    (
      {
        '389ds': {
          'instances': {
            INSTANCE: {
              'config': {
                'slapd': {
                  'root_password': PASS,
                },
                'backend-userroot': {
                  'create_suffix_entry': True,
                  'suffix': SUFFIX,
                },
              },
            },
          },
        },
      },
      {
        'pkg_|-389ds-packages_|-389ds-packages_|-installed': {
          'name': '389ds-packages',
          'result': (None, True),
        },
        f'file_|-389ds-{INSTANCE}-answer-file_|-/root/.389_{INSTANCE}.inf_|-serialize': {
          'name': f'/root/.389_{INSTANCE}.inf',
          'result': (None, True),
        },
        f'cmd_|-389ds-{INSTANCE}-create_|-dscreate -j from-file /root/.389_{INSTANCE}.inf_|-run': {
          'name': f'dscreate -j from-file /root/.389_{INSTANCE}.inf',
          'result': (None, True),
        },
        f'service_|-389ds-{INSTANCE}-start_|-dirsrv@{INSTANCE}_|-running': {
          'name': f'dirsrv@{INSTANCE}',
          'result': (None, True),
        },
      },
    ),

    # 2. pillar with config, replication and replication-agreement
    (
      {
        '389ds': {
          'instances': {
            INSTANCE: {
              'config': {
                'slapd': {
                  'root_password': PASS,
                },
                'backend-userroot': {
                  'create_suffix_entry': True,
                  'suffix': SUFFIX,
                },
              },
              'replication': {
                SUFFIX: {
                  'role': 'supplier',
                  'replica-id': 1,
                  'bind-dn': 'cn=repldude,cn=config',
                  'bind-passwd': '{PBKDF2-SHA512}10000$/0QwvLFeU6V5gkMjc7fH6g$jKmcCTfsP3wlz2ePKRuoJfjcrEANp74Mhs5hOcPPddN3ZgSraWF6YvvaoNYPzzza3FJ7s4worldHSM/A.tT5Jg',
                },
              },
              'replication-agreement': {
                SUFFIX: {
                  'sampleagmtfresh': {
                      'host': 'localhost',
                      'port': '6636',
                      'conn-protocol': 'ldaps',
                      'bind-method': 'simple',
                      'bind-dn': 'cn=replication manager,cn=config',
                      'bind-passwd': 'supersecret',
                  },
                },
              },
            },
          },
        },
      },
      {
        'pkg_|-389ds-packages_|-389ds-packages_|-installed': {
          'name': '389ds-packages',
          'result': (None, True),
        },
        f'file_|-389ds-{INSTANCE}-answer-file_|-/root/.389_{INSTANCE}.inf_|-serialize': {
          'name': f'/root/.389_{INSTANCE}.inf',
          'result': (None, True),
        },
        f'cmd_|-389ds-{INSTANCE}-create_|-dscreate -j from-file /root/.389_{INSTANCE}.inf_|-run': {
          'name': f'dscreate -j from-file /root/.389_{INSTANCE}.inf',
          'result': (None, True),
        },
        f'service_|-389ds-{INSTANCE}-start_|-dirsrv@{INSTANCE}_|-running': {
          'name': f'dirsrv@{INSTANCE}',
          'result': (None, True),
        },
        f'389ds_|-389ds-{INSTANCE}-replication-{SUFFIX}_|-389ds-{INSTANCE}-replication-{SUFFIX}_|-manage_replication': {
          'name': f'389ds-{INSTANCE}-replication-{SUFFIX}',
          'result': (None, True),
          'comment': (
              f'Could not find configuration for instance: {INSTANCE}. Ignoring due to test mode.',
              f'Replication successfully enabled for "{SUFFIX}"',
          ),
        },
        f'389ds_|-389ds-{INSTANCE}-replication-agreement-{SUFFIX}-sampleagmtfresh_|-389ds-{INSTANCE}-replication-agreement-{SUFFIX}-sampleagmtfresh_|-manage_replication_agreement': {
          'name': f'389ds-{INSTANCE}-replication-agreement-{SUFFIX}-sampleagmtfresh',
          'result': (None, True),
          'comment': (
              f'Could not find configuration for instance: {INSTANCE}. Ignoring due to test mode.',
              'Successfully created replication agreement "sampleagmtfresh"',
          ),
        },
      },
    ),

    # 3. pillar with config, data and no clean
    (
      {
        '389ds': {
          'instances': {
            INSTANCE: {
              'config': {
                'slapd': {
                  'root_password': PASS,
                },
                'backend-userroot': {
                  'create_suffix_entry': True,
                  'suffix': SUFFIX,
                },
              },
              'data': {
                'clean': False,
                'tree': {
                  SUFFIX: {
                    'ou=people': {
                      'objectClass': ['organizationalUnit', 'top'],
                      'children': {
                        'cn=Max Mustermannn': {
                          'objectClass': ['inetOrgPerson', 'organizationalPerson', 'person', 'top'],
                          'sn': 'Mustermann',
                          'mail': ['foo@example.com'],
                        },
                      },
                    },
                  },
                },
              },
            },
          },
        },
      },
      {
        'pkg_|-389ds-packages_|-389ds-packages_|-installed': {
          'name': '389ds-packages',
          'result': (None, True),
        },
        f'file_|-389ds-{INSTANCE}-answer-file_|-/root/.389_{INSTANCE}.inf_|-serialize': {
          'name': f'/root/.389_{INSTANCE}.inf',
          'result': (None, True),
        },
        f'cmd_|-389ds-{INSTANCE}-create_|-dscreate -j from-file /root/.389_{INSTANCE}.inf_|-run': {
          'name': f'dscreate -j from-file /root/.389_{INSTANCE}.inf',
          'result': (None, True),
        },
        f'service_|-389ds-{INSTANCE}-start_|-dirsrv@{INSTANCE}_|-running': {
          'name': f'dirsrv@{INSTANCE}',
          'result': (None, True),
        },
        '389ds_|-389ds-data_|-389ds-data_|-manage_data': {
          'changes': (
              {},
              {
                'ou=people,dc=example,dc=com': {
                  'old': None,
                  'new': {'objectClass': ["b'organizationalUnit'", "b'top'"], 'ou': ["b'people'"]},
                },
                'cn=Max Mustermannn,ou=people,dc=example,dc=com': {
                  'old': None,
                  'new': {'objectClass': ["b'inetOrgPerson'", "b'organizationalPerson'", "b'person'", "b'top'"], 'sn': ["b'Mustermann'"], 'mail': ["b'foo@example.com'"], 'cn': ["b'Max Mustermannn'"]},
                },
              },
          ),
          'comment': (
            'Ignoring LDAP error "exception in ldap backend: SERVER_DOWN({\'result\': -1, \'desc\': "Can\'t contact LDAP server", \'errno\': 2, \'ctrls\': [], \'info\': \'No such file or directory\'})" due to test mode.',
            'Successfully updated LDAP entries',
          ),
          'result': (None, True),
        },
      },
    ),

    # 4. pillar with config, data and the default clean
    (
      {
        '389ds': {
          'instances': {
            INSTANCE: {
              'config': {
                'slapd': {
                  'root_password': PASS,
                },
                'backend-userroot': {
                  'create_suffix_entry': True,
                  'suffix': SUFFIX,
                },
              },
              'data': {
                'tree': {
                  SUFFIX: {
                    'ou=people': {
                      'objectClass': ['organizationalUnit', 'top'],
                      'children': {
                        'cn=Max Mustermannn': {
                          'objectClass': ['inetOrgPerson', 'organizationalPerson', 'person', 'top'],
                          'sn': 'Mustermann',
                          'mail': ['foo@example.com'],
                        },
                        'cn=Druck Druckeberger': {
                          'objectClass': ['person', 'printerAbstract', 'top'],
                          'printer-color-supported': True,
                          'sn': 'Druckeberger',
                        },
                      },
                    },
                  },
                },
              },
            },
          },
        },
      },
      {
        'pkg_|-389ds-packages_|-389ds-packages_|-installed': {
          'name': '389ds-packages',
          'result': (None, True),
        },
        f'file_|-389ds-{INSTANCE}-answer-file_|-/root/.389_{INSTANCE}.inf_|-serialize': {
          'name': f'/root/.389_{INSTANCE}.inf',
          'result': (None, True),
        },
        f'cmd_|-389ds-{INSTANCE}-create_|-dscreate -j from-file /root/.389_{INSTANCE}.inf_|-run': {
          'name': f'dscreate -j from-file /root/.389_{INSTANCE}.inf',
          'result': (None, True),
        },
        f'service_|-389ds-{INSTANCE}-start_|-dirsrv@{INSTANCE}_|-running': {
          'name': f'dirsrv@{INSTANCE}',
          'result': (None, True),
        },
        '389ds_|-389ds-data-clean_|-389ds-data-clean_|-manage_data': {
          'changes': {
            'uid=demo_user,ou=people,dc=example,dc=com': {
              'old': {
                'cn': ["b'Demo User'"],
                'displayName': ["b'Demo User'"],
                'gidNuber': ["b'99998'"],
                'homeDirectory': ["b'/var/empty'"],
                'legalName': ["b'Demo User Name'"],
                'loginShell': ["b'/bin/false'"],
                'objectClass': ["b'top'", "b'nsPerson'", "b'nsAccount'", "b'nsOrgPerson'", "b'posixAccount'"],
              },
              'new': None,
            },
          },
          'comment': 'Would change LDAP entries',
          'result': (None, True),
        },
        '389ds_|-389ds-data_|-389ds-data_|-manage_data': {
          'changes': (
              {},
              {
                'ou=people,dc=example,dc=com': {
                  'old': None,
                  'new': {'objectClass': ["b'organizationalUnit'", "b'top'"], 'ou': ["b'people'"]},
                },
                'cn=Max Mustermannn,ou=people,dc=example,dc=com': {
                  'old': None,
                  'new': {'objectClass': ["b'inetOrgPerson'", "b'organizationalPerson'", "b'person'", "b'top'"], 'sn': ["b'Mustermann'"], 'mail': ["b'foo@example.com'"], 'cn': ["b'Max Mustermannn'"]},
                },
                'cn=Druck Druckeberger,ou=people,dc=example,dc=com': {
                  'old': None,
                  'new': {'objectClass': ["b'person'", "b'printerAbstract'", "b'top'"], 'cn': ["b'Druck Druckeberger'"], 'printer-color-supported': ["b'TRUE'"], 'sn': ["b'Druckeberger'"]},
                },
              },
          ),
          'comment': (
            'Ignoring LDAP error "exception in ldap backend: SERVER_DOWN({\'result\': -1, \'desc\': "Can\'t contact LDAP server", \'errno\': 2, \'ctrls\': [], \'info\': \'No such file or directory\'})" due to test mode.',
            'Successfully updated LDAP entries',
          ),
          'result': (None, True),
        },
      },
    ),

    # 5. pillar with config, data, the default clean and an operational attribute
    (
      {
        '389ds': {
          'instances': {
            INSTANCE: {
              'config': {
                'slapd': {
                  'root_password': PASS,
                },
                'backend-userroot': {
                  'create_suffix_entry': True,
                  'suffix': SUFFIX,
                },
              },
              'data': {
                'attributes': ['*', 'aci'],
                'tree': {
                  SUFFIX: {
                    'ou=people': {
                      'aci': '( targetattr = "*" ) ( version 3.0; acl "Self Read"; allow(read, search) (userdn = "ldap:///self"); )',
                      'objectClass': ['organizationalUnit', 'top'],
                      'children': {
                        'cn=Max Mustermannn': {
                          'objectClass': ['inetOrgPerson', 'organizationalPerson', 'person', 'top'],
                          'sn': 'Mustermann',
                          'mail': ['foo@example.com'],
                        },
                      },
                    },
                  },
                },
              },
            },
          },
        },
      },
      {
        'pkg_|-389ds-packages_|-389ds-packages_|-installed': {
          'name': '389ds-packages',
          'result': (None, True),
        },
        f'file_|-389ds-{INSTANCE}-answer-file_|-/root/.389_{INSTANCE}.inf_|-serialize': {
          'name': f'/root/.389_{INSTANCE}.inf',
          'result': (None, True),
        },
        f'cmd_|-389ds-{INSTANCE}-create_|-dscreate -j from-file /root/.389_{INSTANCE}.inf_|-run': {
          'name': f'dscreate -j from-file /root/.389_{INSTANCE}.inf',
          'result': (None, True),
        },
        f'service_|-389ds-{INSTANCE}-start_|-dirsrv@{INSTANCE}_|-running': {
          'name': f'dirsrv@{INSTANCE}',
          'result': (None, True),
        },
        '389ds_|-389ds-data-clean_|-389ds-data-clean_|-manage_data': {
          'changes': {
            'uid=demo_user,ou=people,dc=example,dc=com': {
              'old': {
                'cn': ["b'Demo User'"],
                'displayName': ["b'Demo User'"],
                'gidNuber': ["b'99998'"],
                'homeDirectory': ["b'/var/empty'"],
                'legalName': ["b'Demo User Name'"],
                'loginShell': ["b'/bin/false'"],
                'objectClass': ["b'top'", "b'nsPerson'", "b'nsAccount'", "b'nsOrgPerson'", "b'posixAccount'"],
              },
              'new': None,
            },
          },
          'comment': 'Would change LDAP entries',
          'result': (None, True),
        },
        '389ds_|-389ds-data_|-389ds-data_|-manage_data': {
          'changes': (
              {},
              {
                'ou=people,dc=example,dc=com': {
                  'old': None,
                  'new': {
                      'aci': ["b'( targetattr = \"*\" ) ( version 3.0; acl \"Self Read\"; allow(read, search) (userdn = \"ldap:///self\"); )'"],
                      'objectClass': ["b'organizationalUnit'", "b'top'"],
                      'ou': ["b'people'"],
                  },
                },
                'cn=Max Mustermannn,ou=people,dc=example,dc=com': {
                  'old': None,
                  'new': {'objectClass': ["b'inetOrgPerson'", "b'organizationalPerson'", "b'person'", "b'top'"], 'sn': ["b'Mustermann'"], 'mail': ["b'foo@example.com'"], 'cn': ["b'Max Mustermannn'"]},
                },
              },
          ),
          'comment': (
            'Ignoring LDAP error "exception in ldap backend: SERVER_DOWN({\'result\': -1, \'desc\': "Can\'t contact LDAP server", \'errno\': 2, \'ctrls\': [], \'info\': \'No such file or directory\'})" due to test mode.',
            'Successfully updated LDAP entries',
          ),
          'result': (None, True),
        },
      },
    ),

  ],
  indirect=['pillar'],
)
@pytest.mark.parametrize('test', [True, False])
def test_fresh(host, salt_state_apply, pillar, expect, test):
    out, err, rc = salt_state_apply
    have = reduce_state_out(out)

    # in test mode the LDAP server is not up yet and the data-clean state will not be rendered as a result
    if test and '389ds_|-389ds-data-clean_|-389ds-data-clean_|-manage_data' in expect:
        del expect['389ds_|-389ds-data-clean_|-389ds-data-clean_|-manage_data']

    # we do not do a 1:1 comparison, instead
    #   1. ensure not more states than expected were rendered
    assert len(have) == len(expect)
    #   2. only compare data listed in expected
    # (this allows skipping of fields not relevant to test here, for example comment output from state modules shipped with Salt)
    for expect_state, expect_data in expand_expect_out(expect, test).items():
        assert expect_state in have
        for expect_k, expect_v in expect_data.items():
            assert expect_k in have[expect_state]
            assert have[expect_state][expect_k] == expect_v


@pytest.mark.parametrize(
  'pillar, expect', [

    # 0. pillar with config, replication, replication-agreement, data and no clean - all matching what was already configured by the instance_with_samples fixture
    (
      {
        '389ds': {
          'instances': {
            INSTANCE: {
              'config': {
                'slapd': {
                  'instance_name': INSTANCE,
                  'root_password': PASS,
                  'port': 3389,
                  'secure_port': 6636,
                  'self_sign_cert': False,
                },
                'backend-userroot': {
                  'create_suffix_entry': True,
                  'suffix': SUFFIX,
                  'sample_entries': True,
                },
              },
              'replication': {
                SUFFIX: {
                  'role': 'supplier',
                  'replica-id': '1',
                  'bind-dn': 'cn=replication manager,cn=config',
                  'bind-passwd': 'foo',
                },
              },
              'replication-agreement': {
                SUFFIX: {
                  'sampleagmt': {
                      'host': 'localhost',
                      'port': 3389,
                      'conn-protocol': 'ldap',
                      'bind-method': 'simple',
                      'bind-dn': 'cn=replication manager,cn=config',
                      'bind-passwd': 'foo',
                  },
                },
              },
              'data': {
                'clean': False,
                'tree': {
                  SUFFIX: {
                    'ou=people': {
                      'objectClass': ['top', 'organizationalunit'],
                      'children': {
                        'uid=demo_user': {
                          'objectClass': ['top', 'nsPerson', 'nsAccount', 'nsOrgPerson', 'posixAccount', 'printerAbstract'],
                          'cn': 'Demo User',
                          'displayName': 'Demo User',
                          'homeDirectory': '/var/empty',
                          'legalName': 'Demo User Name',
                          'loginShell': '/bin/false',
                          'uidNumber': 99998,
                          'gidNumber': 99998,
                          'printer-color-supported': False,
                        },
                      },
                    },
                  },
                },
              },
            },
          },
        },
      },
      {
        'pkg_|-389ds-packages_|-389ds-packages_|-installed': {
          'name': '389ds-packages',
        },
        f'file_|-389ds-{INSTANCE}-answer-file_|-/root/.389_{INSTANCE}.inf_|-serialize': {
          'name': f'/root/.389_{INSTANCE}.inf',
        },
        f'cmd_|-389ds-{INSTANCE}-create_|-dscreate -j from-file /root/.389_{INSTANCE}.inf_|-run': {
          'name': f'dscreate -j from-file /root/.389_{INSTANCE}.inf',
        },
        f'service_|-389ds-{INSTANCE}-start_|-dirsrv@{INSTANCE}_|-running': {
          'name': f'dirsrv@{INSTANCE}',
        },
        f'389ds_|-389ds-{INSTANCE}-replication-{SUFFIX}_|-389ds-{INSTANCE}-replication-{SUFFIX}_|-manage_replication': {
          'name': f'389ds-{INSTANCE}-replication-{SUFFIX}',
          'comment': 'Replication configuration is up to date.',
        },
        f'389ds_|-389ds-{INSTANCE}-replication-agreement-{SUFFIX}-sampleagmt_|-389ds-{INSTANCE}-replication-agreement-{SUFFIX}-sampleagmt_|-manage_replication_agreement': {
          'name': f'389ds-{INSTANCE}-replication-agreement-{SUFFIX}-sampleagmt',
          'comment': 'Replication agreement is up to date.',
        },
        '389ds_|-389ds-data_|-389ds-data_|-manage_data': {
          'changes': {},
          'comment': 'LDAP entries already set',
        },
      },
    ),

    # 1. pillar with config, replication, replication-agreement, data and (the default) clean - all matching what was already configured by the instance_with_samples fixture
    (
      {
        '389ds': {
          'instances': {
            INSTANCE: {
              'config': {
                'slapd': {
                  'instance_name': INSTANCE,
                  'root_password': PASS,
                  'port': 3389,
                  'secure_port': 6636,
                  'self_sign_cert': False,
                },
                'backend-userroot': {
                  'create_suffix_entry': True,
                  'suffix': SUFFIX,
                  'sample_entries': True,
                },
              },
              'replication': {
                SUFFIX: {
                  'role': 'supplier',
                  'replica-id': '1',
                  'bind-dn': 'cn=replication manager,cn=config',
                  'bind-passwd': 'foo',
                },
              },
              'replication-agreement': {
                SUFFIX: {
                  'sampleagmt': {
                      'host': 'localhost',
                      'port': '3389',
                      'conn-protocol': 'ldap',
                      'bind-method': 'simple',
                      'bind-dn': 'cn=replication manager,cn=config',
                      'bind-passwd': 'supersecret',
                  },
                },
              },
              'data': {
                'tree': {
                  SUFFIX: {
                    'ou=people': {
                      'objectClass': ['top', 'organizationalunit'],
                      'children': {
                        'uid=demo_user': {
                          'objectClass': ['top', 'nsPerson', 'nsAccount', 'nsOrgPerson', 'posixAccount', 'printerAbstract'],
                          'cn': 'Demo User',
                          'displayName': 'Demo User',
                          'homeDirectory': '/var/empty',
                          'legalName': 'Demo User Name',
                          'loginShell': '/bin/false',
                          'uidNumber': 99998,
                          'gidNumber': 99998,
                          'printer-color-supported': False,
                        },
                      },
                    },
                  },
                },
              },
            },
          },
        },
      },
      {
        'pkg_|-389ds-packages_|-389ds-packages_|-installed': {
          'name': '389ds-packages',
        },
        f'file_|-389ds-{INSTANCE}-answer-file_|-/root/.389_{INSTANCE}.inf_|-serialize': {
          'name': f'/root/.389_{INSTANCE}.inf',
        },
        f'cmd_|-389ds-{INSTANCE}-create_|-dscreate -j from-file /root/.389_{INSTANCE}.inf_|-run': {
          'name': f'dscreate -j from-file /root/.389_{INSTANCE}.inf',
        },
        f'service_|-389ds-{INSTANCE}-start_|-dirsrv@{INSTANCE}_|-running': {
          'name': f'dirsrv@{INSTANCE}',
        },
        f'389ds_|-389ds-{INSTANCE}-replication-{SUFFIX}_|-389ds-{INSTANCE}-replication-{SUFFIX}_|-manage_replication': {
          'name': f'389ds-{INSTANCE}-replication-{SUFFIX}',
          'comment': 'Replication configuration is up to date.',
        },
        f'389ds_|-389ds-{INSTANCE}-replication-agreement-{SUFFIX}-sampleagmt_|-389ds-{INSTANCE}-replication-agreement-{SUFFIX}-sampleagmt_|-manage_replication_agreement': {
          'name': f'389ds-{INSTANCE}-replication-agreement-{SUFFIX}-sampleagmt',
          'comment': 'Replication agreement is up to date.',
        },
        '389ds_|-389ds-data_|-389ds-data_|-manage_data': {
          'changes': {},
          'comment': 'LDAP entries already set',
        },
      },
    ),

    # 2. pillar with config, data, the default clean and operational attributes - all matching what was already configured by the instance_with_samples fixture
    (
      {
        '389ds': {
          'instances': {
            INSTANCE: {
              'config': {
                'slapd': {
                  'instance_name': INSTANCE,
                  'root_password': PASS,
                  'port': 3389,
                  'secure_port': 6636,
                  'self_sign_cert': False,
                },
                'backend-userroot': {
                  'create_suffix_entry': True,
                  'suffix': SUFFIX,
                  'sample_entries': True,
                },
              },
              'data': {
                'attributes': ['*', 'aci'],
                'tree': {
                  SUFFIX: {
                    # test single aci
                    'ou=testou': {
                      # custom aci (from sample ldif in test setup)
                      'aci': '( targetattr = "*" ) ( version 3.0; acl "Self Read"; allow(read, search) (userdn = "ldap:///self"); )',
                      'objectClass': ['top', 'organizationalunit'],
                    },
                    # test multiple acis
                    'ou=people': {
                      'aci': [
                        # default acis (from sample entries enabled with dscreate during test setup)
                        '(targetattr="objectClass || description || nsUniqueId || uid || displayName || loginShell || uidNumber || gidNumber || gecos || homeDirectory || cn || memberOf || mail || nsSshPublicKey || nsAccountLock || userCertificate")(targetfilter="(objectClass=posixaccount)")(version 3.0; acl "Enable anyone user read"; allow (read, search, compare)(userdn="ldap:///anyone");)',
                        '(targetattr="displayName || legalName || userPassword || nsSshPublicKey")(version 3.0; acl "Enable self partial modify"; allow (write)(userdn="ldap:///self");)',
                        '(targetattr="legalName || telephoneNumber || mobile || sn")(targetfilter="(|(objectClass=nsPerson)(objectClass=inetOrgPerson))")(version 3.0; acl "Enable self legalname read"; allow (read, search, compare)(userdn="ldap:///self");)',
                        '(targetattr="legalName || telephoneNumber")(targetfilter="(objectClass=nsPerson)")(version 3.0; acl "Enable user legalname read"; allow (read, search, compare)(groupdn="ldap:///cn=user_private_read,ou=permissions,dc=example,dc=com");)',
                        '(targetattr="uid || description || displayName || loginShell || uidNumber || gidNumber || gecos || homeDirectory || cn || memberOf || mail || legalName || telephoneNumber || mobile")(targetfilter="(&(objectClass=nsPerson)(objectClass=nsAccount))")(version 3.0; acl "Enable user admin create"; allow (write, add, delete, read)(groupdn="ldap:///cn=user_admin,ou=permissions,dc=example,dc=com");)',
                        '(targetattr="uid || description || displayName || loginShell || uidNumber || gidNumber || gecos || homeDirectory || cn || memberOf || mail || legalName || telephoneNumber || mobile")(targetfilter="(&(objectClass=nsPerson)(objectClass=nsAccount))")(version 3.0; acl "Enable user modify to change users"; allow (write, read)(groupdn="ldap:///cn=user_modify,ou=permissions,dc=example,dc=com");)',
                        '(targetattr="userPassword || nsAccountLock || userCertificate || nsSshPublicKey")(targetfilter="(objectClass=nsAccount)")(version 3.0; acl "Enable user password reset"; allow (write, read)(groupdn="ldap:///cn=user_passwd_reset,ou=permissions,dc=example,dc=com");)',
                      ],
                      'objectClass': ['top', 'organizationalunit'],
                      'children': {
                        'uid=demo_user': {
                          'objectClass': ['top', 'nsPerson', 'nsAccount', 'nsOrgPerson', 'posixAccount', 'printerAbstract'],
                          'cn': 'Demo User',
                          'displayName': 'Demo User',
                          'homeDirectory': '/var/empty',
                          'legalName': 'Demo User Name',
                          'loginShell': '/bin/false',
                          'uidNumber': 99998,
                          'gidNumber': 99998,
                          'printer-color-supported': False,
                        },
                      },
                    },
                  },
                },
              },
            },
          },
        },
      },
      {
        'pkg_|-389ds-packages_|-389ds-packages_|-installed': {
          'name': '389ds-packages',
        },
        f'file_|-389ds-{INSTANCE}-answer-file_|-/root/.389_{INSTANCE}.inf_|-serialize': {
          'name': f'/root/.389_{INSTANCE}.inf',
        },
        f'cmd_|-389ds-{INSTANCE}-create_|-dscreate -j from-file /root/.389_{INSTANCE}.inf_|-run': {
          'name': f'dscreate -j from-file /root/.389_{INSTANCE}.inf',
        },
        f'service_|-389ds-{INSTANCE}-start_|-dirsrv@{INSTANCE}_|-running': {
          'name': f'dirsrv@{INSTANCE}',
        },
        '389ds_|-389ds-data_|-389ds-data_|-manage_data': {
          'changes': {},
          'comment': 'LDAP entries already set',
        },
      },
    ),

  ],
  indirect=['pillar'],
)
@pytest.mark.parametrize('test', [True, False])
def test_nochanges(host, instance_with_samples, pillar, test, salt_state_apply, expect):
    out, err, rc = salt_state_apply
    have = reduce_state_out(out)
    assert len(have) == len(expect)

    for expect_state, expect_data in expand_expect_out(expect, test).items():
        assert expect_state in have

        for expect_k, expect_v in expect_data.items():
            assert expect_k in have[expect_state]
            assert have[expect_state][expect_k] == expect_v

        assert have[expect_state]['result'] is True
