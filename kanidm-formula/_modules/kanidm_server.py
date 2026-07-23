import salt.utils
from logging import getLogger

log = getLogger(__name__)
CMD = 'kanidmd'

def __virtual__():
    if salt.utils.path.which(CMD) is None:
        return (False, f'The kanidm_server module cannot be loaded: "{CMD}" is not available.')

    return True

def _run_kanidmd(sub_cmd, expect_out=True, expect_single=True):
    cmd = f'{CMD} -o json {sub_cmd}'
    log.debug(f'Executing: {cmd}')

    return __utils__['kanidm_parse.parse_cli_result'](__salt__['cmd.run_all'](cmd), expect_out, expect_single)

def recover_account(name):
    data = _run_kanidmd(f'recover-account {name}')

    # TODO: kanidm should return with > 0 and print something useful
    if data == 'error':
        return False

    return data.get('password')
