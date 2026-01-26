#!py
# vim: ft=python.salt
from json import load

ETCDIR = '/etc/kanidm'

def _load_pillar():
    with open(__salt__['cp.cache_file']('salt://kanidm/server/defaults.json')) as fh:
        defaults = load(fh)

    return __salt__['pillar.get'](
            'kanidm:server:config',
            default=defaults,
            merge=True, merge_nested_lists=False
    )

def _run_clean():
    states = {}

    states['kanidm-server-packages'] = {
           'pkg.removed': [
               {'names': [
                   'kanidm-server',
               ]}
           ],
    }

    states['kanidm-server-config'] = {
            'file.absent': [
                {'name': f'{ETCDIR}/server.toml'},
            ],
    }

    return states

def _run_manage():
    states = {}
    pillar = _load_pillar()

    states['kanidm-server-packages'] = {
            'pkg.installed': [
                {'pkgs': [
                    'kanidm-server',
                ]}
            ],
    }

    states['kanidm-server-config'] = {
            'file.serialize': [
                {'name': f'{ETCDIR}/server.toml'},
                {'dataset': pillar},
                {'serializer': 'toml'},
                {'user': 'root'},
                {'group': 'root'},
                {'mode': '0644'},
            ],
    }

    states['kanidm-server-service'] = {
            'service.running': [
                {'name': 'kanidmd'},
                {'enable': True},
                {'reload': True},
                {'watch': [
                    {'file': 'kanidm-server-config'},
                ]},
            ],
    }

    #states['kanidm-server-salt-admin'] = {
    #        'cmd.run': [
    #            {'name': 'kanidmd recover-account admin 

    return states

def run():
    states = {}

    if 'config' in __salt__['pillar.get']('kanidm:server', {}):
        return _run_manage()
    else:
        return _run_clean()
