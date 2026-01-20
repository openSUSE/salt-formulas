"""
Salt state module for 389-DS
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

def manage_data(name, entries, connect_spec):
    """
    This is a wrapper over ldap.managed softening the exception handling to avoid state failure if the LDAP server does not yet exist but would be created during a state run.
    """
    out = None

    try:
        out = __states__['ldap.managed'](name, entries, connect_spec)
    # LDAPError (from salt.modules.ldap3 or from ldap) does not match here albeit being printed, possibly because loading happens through
    # salt.loaded.int.module which cannot be imported
    #except LDAPError as e:
    except Exception as e:
        if __opts__['test']:
            out = {'name': name, 'result': None, 'changes': {}, 'comment': f'Ignoring LDAP error "{e}" due to test mode.'}

        if not out:
            raise
    except:
        raise

    return out


def _diff_attrs(attrs_have, attrs_want):
    changes = {}

    for attr, val_want in attrs_want.items():
        val_have = attrs_have[attr][0]

        if val_have != val_want:
            if not 'new' in changes and not 'old' in changes:
                changes['new'] = {}
                changes['old'] = {}

            changes['old'][attr] = val_have
            changes['new'][attr] = val_want

    return changes


def manage_replication(name, instance, suffix, role, replica_id, bind_dn, bind_passwd):
    """
    This configures and, for a few values, updates replication for a given suffix.
    """
    ret = {'name': name, 'result': None, 'comment': '', 'changes': {}}

    have, ok = __salt__['389ds.replication_get'](instance, suffix)
    if not ok and 'desc' in have:
        ret['comment'] = have['desc'] + '.'

        # dsconf or the instance might not exist yet
        if __opts__['test']:
            ret['comment'] = ret['comment'] + ' Ignoring due to test mode.'
            return ret

        ret['result'] = False
        return ret

    reinit = not have

    if have:
        ret['changes'] = _diff_attrs(have['attrs'], {
                'nsds5replicaid': str(replica_id),
                'nsds5replicabinddn': bind_dn,
                # TODO: figure out what to compare other fields against
                # 'nsds5replicatype':
                # ??? str(__salt__['389ds.replicatype_from_string'](role)),
        })

        if ret['changes']:
            if __opts__['test']:
                ret['comment'] = f'Would delete and re-create the replication for {suffix}.'
                return ret

            res, ok = __salt__['389ds.replication_disable'](instance, suffix)
            if res and ok:
                ret['comment'] = res + '\n'  # "Replication disabled for ..."
                reinit = True
            else:
                ret['comment'] = res
                ret['result'] = False
                return ret
        else:
            ret['comment'] = 'Replication configuration is up to date.'
            ret['result'] = True
            return ret

    if reinit:
        if not ret['changes']:
            ret['changes'] = {
                    'new': {
                        'nsds5replicaid': replica_id,
                    },
        }

        if __opts__['test']:
            ret['comment'] = f'Would create replication for {suffix}.'
            return ret

        res, ok = __salt__['389ds.replication_enable'](instance, suffix, role, replica_id, bind_dn, bind_passwd)
        ret['comment'] = ret['comment'] + str(res)  # "Replication successfully enabled for ..." or JSON with error
        ret['result'] = ok

    return ret


def manage_replication_agreement(name, instance, suffix, agmt_name=None, host=None, port=None, conn_protocol=None, bind_dn=None, bind_passwd=None, bind_method=None):
    """
    This configures and updates a replication agreement for a given suffix.
    """
    if agmt_name is None:
        agmt_name = name

    ret = {'name': name, 'result': None, 'comment': '', 'changes': {}}
    if agmt_name is None:
        agmt_name = name

    have, ok = __salt__['389ds.repl_agmt_get'](instance, suffix, agmt_name)
    if not ok and 'desc' in have:
        ret['comment'] = have['desc'] + '.'

        # dsconf or the instance might not yet exist
        if __opts__['test']:
            ret['comment'] = ret['comment'] + ' Ignoring due to test mode.'
            return ret

        ret['result'] = False
        return ret

    attrs_want = {
            'nsds5replicahost': host,
            'nsds5replicaport': str(port),  # dsconf returns it as a string, cast our input for comparison
            'nsds5replicatransportinfo': conn_protocol,
            'nsds5replicabindmethod': bind_method,
            'nsds5replicabinddn': bind_dn,
            #'nsds5replicacredentials': # cannot be compared, reference the comment in pillar.example
    }

    if have:
        attrs_have = have['attrs']
        ret['changes'] = _diff_attrs(attrs_have, attrs_want)

        if not ret['changes']:
            ret['comment'] = 'Replication agreement is up to date.'
            ret['result'] = True

            return ret

        if __opts__['test']:
            ret['comment'] = 'Would update the replication agreement.'

            return ret

        res, ok = __salt__['389ds.repl_agmt_set'](
                instance, suffix, agmt_name, host, port, conn_protocol, bind_dn, bind_passwd, bind_method
        )

    else:
        ret['changes'] = {
                'new': {}
        }

        for attr, val in attrs_want.items():
            if val is not None:
                ret['changes']['new'][attr] = val

        if __opts__['test']:
            ret['comment'] = 'Would create replication agreement.'

            return ret

        res, ok = __salt__['389ds.repl_agmt_create'](
                instance, suffix, agmt_name, host, port, conn_protocol, bind_dn, bind_passwd, bind_method
        )

    ret['comment'] = res
    ret['result'] = ok

    return ret
