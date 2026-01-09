from asyncio import run
from salt.exceptions import CommandNotFoundError
from salt.utils.path import which
from logging import getLogger

log = getLogger(__name__)
CMD = 'kanidm'

HAVE_KANIDM_CLI = None
HAVE_KANIDM_PY = None
client = None

if which(CMD) is None:
    HAVE_KANIDM_CLI = False
else:
    HAVE_KANIDM_CLI = True

def _py_client():
    # TODO: error handling and factor out path
    with open('/etc/kanidm/salt') as fh:
        uri, token = fh.readlines()
    #__salt__['pillar.get']('kanidm:server:config:origin', __salt__['pillar.get']('kanidm:client:config:uri'))

    return KanidmClient(uri=uri.strip(), token=token.strip())

    #log.error('The kanidm_client module cannot locate a Kanidm server URI. API functionality will not be available.')
    #HAVE_KANIDM_PY = False
    #return None

try:
    from kanidm import KanidmClient
    HAVE_KANIDM_PY = True
    client = _py_client()
except ImportError:
    HAVE_KANIDM_PY = False

def __virtual__():
    if not HAVE_KANIDM_CLI and not HAVE_KANIDM_PY:
        return (False, f'The kanidm_client module cannot be loaded: neither the "{CMD}" binary nor pykanidm are available.')

    return True

def _guard_cli():
    if not HAVE_KANIDM_CLI:
        raise CommandNotFoundError(f'Execution not possible: "{CMD}" is not available.')

def _guard_py():
    if not HAVE_KANIDM_PY:
        raise CommandNotFoundError(f'Execution not possible: pykanidm is not available.')

def _run_kanidm(sub_cmd, expect_out=True, expect_single=True, user=None, env={}):
    _guard_cli()

    base_cmd = f'{CMD} -o json'

    if user is not None:
        base_cmd = f'{base_cmd} -D {user}'

    cmd = f'{base_cmd} {sub_cmd}'
    log.debug(f'Executing: {cmd}')

    return __utils__['kanidm_parse.parse_cli_result'](__salt__['cmd.run_all'](cmd, env=env), expect_out, expect_single)

def local_login(user, password):
    """
    This is used internally for bootstrapping through local_* functions. Do not use it on the command line!
    """
    return _run_kanidm('login', expect_out=False, user=user, env={'KANIDM_PASSWORD': password})

def local_service_account_create(account_id, display_name, managed_by, groups=[]):
    data = _run_kanidm(f'service-account create {account_id} "{display_name}" {managed_by}', expect_out=False)
    if data is True:
        for group in groups:
            _run_kanidm(f'group add-members {group} {account_id}')

        return True

    return False

def local_service_account_api_token(account_id, label, expiry=None, rw=False):
    cmd = f'service-account api-token generate {account_id}'
    if expiry is not None:
        cmd = f'{cmd} {expiry}'
    if rw is True:
        cmd = f'{cmd} -w'

    return _run_kanidm(cmd).get('result')

def service_account_get(name):
    _guard_py()

    try:
        return run(client.service_account_get(name)).dict()
    except ValueError:
        return None

def service_account_list():
    _guard_py()

    # TODO: https://github.com/kanidm/kanidm/issues/4044
    return None

def person_account_create(name, displayname):
    _guard_py()

    r = run(client.person_account_create(name, displayname))
    log.debug(f'person_account_create(): got {r.dict()}')
    return r.status_code == 200

def person_account_update(name, newname=None, displayname=None, legalname=None, mail=None):
    _guard_py()

    r = run(client.person_account_update(name, newname, displayname, legalname, mail))
    log.debug(f'person_account_update(): got {r.dict()}')
    return r.status_code == 200

def person_account_get(name):
    _guard_py()

    try:
        return run(_person_account_get(name))
    except ValueError:
        return None

async def _person_account_list():
    return await client.person_account_list()

def person_account_list():
    _guard_py()

    return __utils__['kanidm_parse.parse_list_result'](run(_person_account_list()))
