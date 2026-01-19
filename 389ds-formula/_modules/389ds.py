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
        '--replica-id', str(replica_id),
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


def repl_agmt_list(instance, suffix):
    """
    This wraps "dsconf repl-agmt list".
    """
    out, _ = _dsconf(instance, ['replication', 'list', '--suffix', suffix])
    return out.get('items')


def repl_agmt_create(instance, suffix, agmt_name, host, port, conn_protocol, bind_dn, bind_passwd, bind_method):
    """
    This wraps "dsconf repl-agmt create".
    """
    return _dsconf(instance, [
        'repl-agmt', 'create',
        '--suffix', suffix,
        '--host', host,
        '--port', str(port),
        '--conn-protocol', conn_protocol,
        '--bind-dn', bind_dn,
        '--bind-passwd', bind_passwd,
        '--bind-method', bind_method,
        agmt_name,
    ])


def repl_agmt_delete(instance, suffix, agmt_name):
    """
    This wraps "dsconf repl-agmt delete".
    """
    return _dsconf(instance, [
        'repl-agmt', 'delete',
        '--suffix', suffix,
        agmt_name,
    ])


def repl_agmt_enable(instance, suffix, agmt_name):
    """
    This wraps "dsconf repl-agmt enable".
    """
    return _dsconf(instance, [
        'repl-agmt', 'enable',
        '--suffix', suffix,
        agmt_name,
    ])


def repl_agmt_disable(instance, suffix, agmt_name):
    """
    This wraps "dsconf repl-agmt disable".
    """
    return _dsconf(instance, [
        'repl-agmt', 'disable',
        '--suffix', suffix,
        agmt_name,
    ])


def repl_agmt_get(instance, suffix, agmt_name):
    """
    This wraps "dsconf repl-agmt get".
    """
    out, ok = _dsconf(instance, [
        'repl-agmt', 'get',
        '--suffix', suffix,
        agmt_name,
    ])

    if 'desc' in out:
        if 'No object exists given the filter criteria:' in out['desc'] \
                or 'Could not find the agreement' in out['desc']:
            return {}, ok

    return out, ok


def repl_agmt_init(instance, suffix, agmt_name):
    """
    This wraps "dsconf repl-agmt init".
    """
    return _dsconf(instance, [
        'repl-agmt', 'init',
        '--suffix', suffix,
        agmt_name,
    ])


def repl_agmt_set(instance, suffix, agmt_name, host=None, port=None, conn_protocol=None, bind_dn=None, bind_passwd=None, bind_method=None):
    """
    This wraps "dsconf repl-agmt set".
    """
    args = []

    if host is not None:
        args.extend(['--host', host])
    if port is not None:
        args.extend(['--port', str(port)])
    if conn_protocol is not None:
        args.extend(['--conn-protocol', conn_protocol])
    if bind_dn is not None:
        args.extend(['--bind-dn', bind_dn])
    if bind_passwd is not None:
        args.extend(['--bind-passwd', bind_passwd])
    if bind_method is not None:
        args.extend(['--bind-method', bind_method])

    args.append(agmt_name)

    return _dsconf(instance, [
        'repl-agmt', 'set',
        '--suffix', suffix,
    ] + args)


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
