from json.decoder import JSONDecodeError
from salt.exceptions import CommandExecutionError
from salt.utils.json import loads
from logging import getLogger

log = getLogger(__name__)

def parse_cli_result(out, expect_out=True, expect_single=True):
    log.debug(f'Result: {out}')

    # for commands such as "login" which do not produce json at all
    if expect_out is False:
        if out['retcode'] == 0:
            return True
        return False

    if out['retcode'] != 0:
        raise CommandExecutionError(f'Execution of "kanidmd" failed: {out}')

    if not out['stdout']:
        return True

    res = None

    try:
        res = loads(out['stdout'])
    except JSONDecodeError:
        # sometimes the result is on stdout, sometimes on stderr
        try:
            res = loads(out['stderr'])
        except JSONDecodeError:
            # https://github.com/kanidm/kanidm/issues/4040
            data = []
            for line in out['stdout'].splitlines() + out['stderr'].splitlines():
                if not ( line[0] == '{' or ( line[0] == '"' and line[-1] == '"' ) ):
                    continue
                data.append(loads(line))
            
            ld = len(data)
            if ld == 1 and expect_single:
                res = data[0]
            elif ld > 1 and not expect_single:
                res = data

    if res is not None:
        return res

    raise CommandExecutionError(f'Execution of "kanidmd" did not yield expected JSON data: {out}')

def parse_list_result(data):
    res = []

    for obj in data:
        res.append(obj.dict())

    return res
