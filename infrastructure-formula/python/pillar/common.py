"""
Copyright (C) 2024-2025 Georg Pfuetzenreuter <mail+opensuse@georg-pfuetzenreuter.net>

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

from logging import getLogger

from yaml import safe_load

log = getLogger(__name__)

def use_domains(domain):
    return domain != 'infra.opensuse.org'

def pillar_path():
    return '/srv/salt-git/pillar'

def pillar_domain_path(domain):
    root = pillar_path()

    if use_domains(domain):
        return f'{root}/domain/{domain.replace(".", "_")}'
    else:
        return f'{root}/infra'

def pillar_domain_data(domain, datasets, site=None):
    domaindir = pillar_domain_path(domain)
    domaindata = {}

    for dataset in datasets:
        with open(f'{domaindir}/{dataset}.yaml') as fh:
            data = safe_load(fh)

            if use_domains(domain) or dataset != 'networks':
                log.debug(f'network.common using full dataset "{dataset}"')
                domaindata[dataset] = data
            else:
                log.debug(f'network.common: trying site inside dataset "{dataset}"')
                if site is None:
                    log.warn('network.common: no site')
                    continue

                domaindata[dataset] = data.get(site, {})

    return domaindata
