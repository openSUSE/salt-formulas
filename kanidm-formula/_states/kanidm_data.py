BUILTIN_ACCOUNTS = []

def person_account_managed(name, domain, account_data):
    ret = {'name': name, 'changes': {}, 'result': None, 'comment': ''}

    have_accounts_list = __salt__['kanidm_client.person_account_list']()
    # TODO: not efficient to do this on every call
    have_accounts = {}
    for p in have_accounts_list:
        name = p.pop('name')
        if name:
            have_accounts[name] = p

    if name in have_accounts:
        fields = ['displayname', 'legalname', 'mail']
        update_fields = {
                field: None
                for field in fields
        }
        for field in fields:
            if field in account_data:
                if account_data[field] != have_accounts[name].get(field):
                    if name not in ret['changes']:
                        ret['changes'][name] = {}
                    if field not in ret['changes'][name]:
                        ret['changes'][name][field] = {}

                    ret['changes'][name][field]['new'] = account_data[field]
                    ret['changes'][name][field]['old'] = have_accounts[name][field]
                    update_fields[field] = account_data[field]

            elif field in have_accounts[name]:
                if name not in ret['changes']:
                    ret['changes'][name] = {}
                ret['changes'][name][field] = {
                        'new': None,
                        'old': have_accounts[name][field],
                }

        if name in ret['changes']:
            if __opts__['test']:
                ret['comment'] = 'Account would be updated.'
                ret['result'] = None
            else:
                ret['result'] = __salt__['kanidm_client.person_account_update'](name, displayname=update_fields['displayname'], legalname=update_fields['legalname'], mail=update_fields['mail'])
                if ret['result'] is True:
                    ret['comment'] = 'Account updated.'
                else:
                    ret['comment'] = 'Account update failed.'

        else:
            ret['comment'] = 'Account is up to date.'
            ret['result'] = True

    elif __opts__['test']:
        ret['comment'] = 'Account would be created.'
        ret['result'] = None

    else:
        ret['result'] = __salt__['kanidm_client.person_account_create'](name, displayname=account_data.get('displayname'))
        if ret['result'] is True:
            ret['comment'] = 'Account created.'
        else:
            ret['comment'] = 'Account creation failed.'

    return ret


#def person_accounts_managed(domain, persons_pillar):
#    want_persons = __salt__['pillar.get'](persons_pillar)
#    have_persons_list = __salt__['kanidm_client.person_account_list')
#    reduced_have_persons = []
#    have_names = []
#
#    have_persons = {}
#    for p in have_persons_list:
#        name = p.pop('name')
#        if name:
#            have_persons[name] = p
#
#    add_persons = []
#    update_persons = []
#    delete_persons = []
#
#    for name, more in want_persons:
#        if name in have_persons:
#            update_persons.append(name)
#        if name not in have_persons:
#            add_persons.append(name)
#    for name, more in have_persons:
#        if name not in want_persons and name not in BUILTIN_ACCOUNTS:
#            delete_persons.append(name)
