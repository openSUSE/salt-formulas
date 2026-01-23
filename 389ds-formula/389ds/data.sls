#!py
"""
vim: ft=python.salt

Salt states for managing LDAP objects in 389-DS
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

from logging import getLogger

from ldap import DECODING_ERROR
from ldap.dn import str2dn

log = getLogger(__name__)


def _connect_spec(instance):
    """
    Returns a LDAP connection object.
    So far, this only handles local SASL EXTERNAL authentication.
    """
    return {
        'url': f'ldapi://%2frun%2fslapd-{instance}.socket',
        # the bind setup is a bit of a cludge because sasl_non_interactive_bind_s() is not exposed in Salt's ldap3 module
        # would be nice to implement it there, but probably https://github.com/salt-extensions/saltext-ldap/issues/1 should
        # be done before adding new features
        'bind': {
            'method': 'sasl',
            'mechanism': 'sasl',
            'credentials': {
                'args': [
                    {'0x4001': ''},  # ldap.sasl.CB_USER
                ],
                'kwargs': {
                    'mech': 'external',
                },
            },
        },
    }


def _attr_from_dn(dn):
    """
    Helper to get an attribute/value pair from the first element of the given distinguished name (DN).
    """
    try:
        dn_ava = str2dn(dn)
    except DECODING_ERROR:
        log.error(f'Cannot parse DN "{dn}", skipping.')
        return ()

    log.debug(f'Got AVA DN: {dn_ava}')

    for e in dn_ava:
        if len(e) > 1:
            log.error(f'Unexpected explosion of DN "{dn}", skipping.')
            return ()

        a, v, i = e[0]

        return (a, v)


def _entry(dn, attrs):
    new_attrs = {}

    for attr, vals in attrs.items():
        # probably not needed here, because we pop children before passing data
        if attr == 'children':
            continue

        if not isinstance(vals, list):
            vals = [vals]

        new_attrs[attr] = []

        for val in vals:
            if val is True or val is False:
                val = str(val).upper()

            new_attrs[attr].append(val)

    dn_a, dn_v = _attr_from_dn(dn)

    if dn_a is None or dn_v is None:
        # DN is probably not valid and an error was printed about it already
        return {}

    if dn_a not in new_attrs:
        new_attrs[dn_a] = [dn_v]

    return {
            dn: [
                {'delete_others': True},
                #{'strict_order': True},   # pending patch
                {'replace': new_attrs},
            ],
    }


def _entries(dn, data, parent_dn=None):
    """
    Helper to construct a list of entries as expected by ldap.managed.
    This recurses down the tree using a special "children" attribute.
    """
    out_dns = []
    out_entries = []
    out_clean = {}

    if not data:
        return out_dns, out_entries

    if parent_dn is not None:
        dn = f'{dn},{parent_dn}'

    children = data.pop('children', {})
    clean = data.pop('clean', None)

    # in case of children, we always want to know whether subordinates are to be cleaned up
    # in case of no children however, this is only tracked if an explicit clean choice was passed
    # (otherwise we risk useless LDAP searches for every single leaf object further down if the inherited clean choice is True)
    if children or clean is not None:
        out_clean[dn] = clean

    out_dns.append(dn)
    out_entries.append(_entry(dn, data))

    for child_dn, child_data in children.items():
        c_dns, c_entries, c_clean = _entries(child_dn, child_data, dn)
        out_dns.extend(c_dns)
        out_entries.extend(c_entries)
        out_clean.update(c_clean)

    return out_dns, out_entries, out_clean


def _search(cs, base):
    try:
        results = __salt__['ldap3.search'](cs, base=base, scope='onelevel', attrlist=['dn'])

    # cannot handle LDAPError specificially here because it comes through salt.loaded.int.module
    except Exception as e:
        log.debug(f'Exception from ldap3.search: {e}.')
        results = []

    return results


def _entry_clean(dn):
    log.debug(f'Marking DN "{dn}" for removal.')

    return {
        dn: [
            {'delete_others': True},
            {'delete': {}},
        ],
    }


def run():
    states = {}

    for name, config in __salt__['pillar.get']('389ds:instances', {}).items():
        if 'data' in config:
            dns_want = []
            entries_want = []
            entries_drop = []

            cs = _connect_spec(name)

            attributes = config['data'].get('attributes', [])
            clean = config['data'].get('clean', True)

            for suffix, parents in config['data'].get('tree', {}).items():

                for parent, data in parents.items():
                    p_dn = f'{parent},{suffix}'
                    log.debug(f'Traversing into "{p_dn}".')

                    p_clean = data.pop('clean', clean)
                    sub_dns, sub_entries, sub_cleans = _entries(p_dn, data)
                    dns_want.extend(sub_dns)
                    entries_want.extend(sub_entries)

                    for sub_dn, sub_clean in sub_cleans.items():
                        log.debug(f'Detecting cleaning preference for "{sub_dn}".')

                        if sub_clean is None:
                            sub_clean = p_clean

                        if not sub_clean:
                            log.debug(f'Skipping cleaning of child "{sub_dn}".')
                            continue

                        log.debug(f'Starting cleaning of child "{sub_dn}".')

                        for existing_dn in _search(cs, sub_dn):
                            if existing_dn not in dns_want and existing_dn != p_dn:
                                entries_drop.append(_entry_clean(existing_dn))

            if entries_drop:
                states['389ds-data-clean'] = {
                        '389ds.manage_data': [
                            {'connect_spec': cs},
                            {'entries': entries_drop},
                        ],
                }


            states['389ds-data'] = {
                    '389ds.manage_data': [
                        {'connect_spec': cs},
                        {'entries': entries_want},
                    ],
            }

            if attributes:
                states['389ds-data']['389ds.manage_data'].append({
                    'attrlist': attributes,
                })

    return states
