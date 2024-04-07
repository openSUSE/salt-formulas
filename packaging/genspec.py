#!/usr/bin/python3
# Tool to generate an infrastructure-formulas.spec file
# Copyright (C) 2023-2024 Georg Pfuetzenreuter <mail+rpm@georg-pfuetzenreuter.net>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import logging
import sys
from argparse import ArgumentParser

pattern = '-formula'
infile  = 'packaging/templates/infrastructure-formulas.spec.j2'
outfile = 'infrastructure-formulas.spec'

argp = ArgumentParser()
argg = argp.add_mutually_exclusive_group()
argg.add_argument('-v', help='Print verbose output', action='store_const', dest='loglevel', const=logging.INFO, default=logging.WARNING)
argg.add_argument('-d', help='Print very verbose output', action='store_const', dest='loglevel', const=logging.DEBUG, default=logging.INFO)
args = argp.parse_args()

logging.basicConfig()
log = logging.getLogger('genspec')
log.setLevel(args.loglevel)

def abort(msg):
    log.error(msg)
    sys.exit(1)

try:
    from jinja2 import Template
except ImportError as myerror:
    abort('Missing jinja2 library')

from pathlib import Path
import yaml

if not Path.is_dir(Path('packaging')):
    abort('Please call this program from the repository root')

directories = sorted(Path('.').glob('*{}/'.format(pattern)))

formulas = {}
for directory in directories:
    formula = str(directory).removesuffix(pattern)
    log.info('Formula: {}'.format(formula))
    metadata = '{}/metadata/metadata.yml'.format(directory)
    if Path.is_file(Path(metadata)):
        with open(metadata) as yml:
            meta = yaml.safe_load(yml)
        summary = meta.get('summary', None)
        description = meta.get('description', None)
        lic = meta.get('license', None)
        requires = meta.get('require', [])
    else:
        log.warning('No metadata file for {}'.format(formula))
        summary = None
        description = None
    if summary is None:
        abort('Cannot proceed without at least a summary in the metadata file for the {} formula'.format(formula))
    log.info('Summary: {}'.format(str(summary)))
    log.info('Description: {}'.format(str(description)))
    log.info('License: {}'.format(str(lic)))
    if any([Path.is_file(Path('{}/{}'.format(directory, file))) for file in ['COPYING', 'LICENCE', 'LICENSE']]) and lic is None:
        log.warning('Formula {} ships a custom license, but does not declare it in its metadata. Make sure to update the generated spec file!'.format(formula))
        lic = 'FIX-ME'
    formulas.update({formula: {'summary': summary, 'description': description, 'license': lic, 'requires': requires}})

log.debug(formulas)

with open(infile, 'r') as j2:
    template = Template(j2.read())

rendered = template.render(formulas=formulas)
log.debug(rendered)

with open(outfile, 'w') as spec:
    spec.write(rendered)

log.info('Wrote {}'.format(outfile))
