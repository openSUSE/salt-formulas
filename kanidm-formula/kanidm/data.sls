#!py
# vim: ft=python.salt

def run():
  states = {}
  pillar = __salt__['pillar.get']('kanidm:data', {})

  for name, data in pillar.get('person_accounts', {}).items():
    states[f'kanidm-data-person-account-{name}'] = {
            'kanidm_data.person_account_managed': [
                {'name': name},
                {'domain': pillar.get('domain', '')},  # TODO
                {'account_data': data},
            ],
    }

  return states
