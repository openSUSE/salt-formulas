"""
Salt state module for managing lockfiles
Copyright (C) 2023 Georg Pfuetzenreuter <mail+opensuse@georg-pfuetzenreuter.net>

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

from pathlib import Path

def lock(name, path='/var/lib/salt/'):
    ret = {'name': name, 'result': False, 'changes': {}, 'comment': ''}
    lockfile = path + name
    if Path(lockfile).exists():
        if __opts__["test"]:
            ret["comment"] = "Would have complained about {0} already existing".format(lockfile)
            ret["result"] = None
        else:
            ret['comment'] = 'Lockfile {0} already exists'.format(lockfile)
        return(ret)
    if __opts__["test"]:
        ret["comment"] = "Lockfile {0} would have been created".format(lockfile)
        ret["result"] = None
        return(ret)
    try:
        Path(lockfile).touch(exist_ok=False)
    except FileExistsError as error:
        ret['comment'] = 'Failed to create lockfile {0}, it already exists'.format(lockfile)
        return(ret)
    except Exception as error:
        ret['comment'] = 'Failed to create lockfile {0}, error: {1}'.format(lockfile, error)
        return(ret)
    if Path(lockfile).exists():
        ret['comment'] = 'Lockfile {0} created'.format(lockfile)
        ret['result'] = True
    else:
        ret['comment'] = 'Failed to create lockfile {0}'.format(lockfile)
    return(ret)

def unlock(name, path='/var/lib/salt/'):
    ret = {'name': name, 'result': False, 'changes': {}, 'comment': ''}
    lockfile = path + name
    if not Path(lockfile).exists():
        if __opts__["test"]:
            ret['comment'] = 'Lockfile {0} would have been removed if it existed'.format(lockfile)
            ret["result"] = None
        else:
            ret['comment'] = 'Lockfile {0} does not exist'.format(lockfile)
        return(ret)
    if __opts__["test"]:
        ret["comment"] = "Lockfile {0} would have been removed".format(lockfile)
        ret["result"] = None
        return(ret)
    try:
        Path(lockfile).unlink()
    except Exception as error:
        ret['comment'] = 'Failed to delete lockfile {0}, error: {1}'.format(lockfile, error)
        return(ret)
    if not Path(lockfile).exists():
        ret['comment'] = 'Lockfile {0} deleted'.format(lockfile)
        ret['result'] = True
    else:
        ret['comment'] = 'Failed to delete lockfile {0}'.format(lockfile)
    return(ret)

def check(name, path='/var/lib/salt/'):
    ret = {'name': name, 'result': False, 'changes': {}, 'comment': ''}
    lockfile = path + name
    if __opts__["test"]:
        ret["comment"] = "Would have checked for existence of lockfile {0}".format(lockfile)
        ret["result"] = None
        return(ret)
    if Path(lockfile).exists():
        ret['comment'] = 'Deployment of {0} is locked via {1} - maybe there is an existing execution'.format(name, lockfile)
    else:
        ret['comment'] = '{0} is not locked'.format(name)
        ret['result'] = True
    return(ret)
