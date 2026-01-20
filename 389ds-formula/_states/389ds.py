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
        for attr, want_val in {
                'nsds5replicaid': str(replica_id),
                'nsds5replicabinddn': bind_dn,
                # TODO: figure out what to compare other fields against
                # 'nsds5replicatype':
                # ??? str(__salt__['389ds.replicatype_from_string'](role)),
        }.items():
            want_val = [want_val]
            if have['attrs'][attr] != want_val:
                ret['changes'][attr] = {
                        'old': have['attrs'][attr],
                        'new': want_val,
                }

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
