"""
Salt execution module for 389-DS
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

from json import JSONDecodeError, loads
from logging import getLogger
from shlex import join

log = getLogger(__name__)

def _dsconf(instance, args):
    cmd = join(['/usr/sbin/dsconf', '-j', instance] + args)
    log.debug(f'Executing: {cmd}')

    out = __salt__['cmd.run_all'](
            cmd=cmd,
            shell='/bin/sh',
            python_shell=False,
            clean_env=True,
            timeout=15,
            redirect_stderr=True,  # JSON is not written to the same fd consistently
    )
    log.debug(f'Return: {out}')
    ok = out['retcode'] == 0

    try:
        return loads(out['stdout']), ok

    except JSONDecodeError:
        #raise CommandExecutionError(f'Failed to parse output: {out}')
        # some dsconf commands don't return json at all, some only on error ..
        return out['stdout'], ok


def replication_list(instance):
    """
    This wraps "dsconf replication list".
    """
    out, ok = _dsconf(instance, ['replication', 'list'])
    return out.get('items')


def replication_enable(instance, suffix, role, replica_id, bind_dn, bind_passwd):
    """
    This wraps "dsconf replication enable" and enables replication for a given suffix.
    The function arguments are similar to the command line arguments expected by dsconf.
    """
    out, ok = _dsconf(instance, [
        'replication', 'enable',
        '--suffix', suffix,
        '--role', role,
        '--replica-id', replica_id,
        '--bind-dn', bind_dn,
        '--bind-passwd', bind_passwd,
    ])

    return out, ok


def replication_disable(instance, suffix):
    """
    This wraps "dsconf replication disable" and disables replication for a given suffix.
    """
    out, ok = _dsconf(instance, [
        'replication', 'disable',
        '--suffix', suffix,
    ])

    return out, ok


def replication_get(instance, suffix):
    """
    This wraps "dsconf replication get".
    """
    out, ok = _dsconf(instance, [
        'replication', 'get',
        '--suffix', suffix,
    ])

    if 'desc' in out:
        if 'No object exists given the filter criteria:' in out['desc']:
            return {}, ok

    return out, ok


def replicarole_from_string(rt):
    """
    This map strings to lib389.ReplicaRole enums.
    The values are hardcoded due to lib389 not always being available.
    """
    if rt == 'leaf':
        return 1  # ReplicaRole.CONSUMER
    if rt == 'hub':
        return 2  # ReplicaRole.HUB
    if rt == 'supplier':
        return 3  # ReplicaRole.SUPPLIER
    if rt == 'standalone':
        return 4  # ReplicaRole.STANDALONE
