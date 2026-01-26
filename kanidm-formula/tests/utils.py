from json import loads

def salt(host, command):
    print(command)
    result = host.run(f'sudo salt-call --local --out json {command}')
    print(result)
    output = loads(result.stdout)['local']
    return output, result.stderr, result.rc
