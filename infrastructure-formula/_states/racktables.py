"""
Salt state module for managing RackTables entries
Copyright (C) 2023-2024 SUSE LLC <georg.pfuetzenreuter@suse.com>

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

import MySQLdb
import rtapi
import logging
from salt.exceptions import CommandExecutionError
log = logging.getLogger(__name__)

# to-do: consider moving some logic to an execution module
# to-do: update existing entry if VM specifications changed
# to-do: repair MAC address formatting bug
# won't fix: use an IPAM tool with a REST API ...

def _connect(db_host, db_user, db_secret, db):
    try:
        dbhandle = MySQLdb.connect(host=db_host, user=db_user, passwd=db_secret, db=db)
        return(rtapi.RTObject(dbhandle))
    except MySQLdb.Error as err:
        log.critical("RackTables MySQL Error: %s" % str(err))
        # it would be nicer to raise this without an ugly Salt exception stacktrace given Salt additionally prints the MySQL stacktrace beforehand
        raise CommandExecutionError('RackTables MySQL connection failure')

def vm(db_host, db_user, db_secret, db, name, interfaces, ram, city, usage):
    ret = {'name': name, 'result': True, 'changes': {}, 'comment': ''}
    rt = _connect(db_host, db_user, db_secret, db)

    if rt.ObjectExistName(name):
        objid=rt.GetObjectId(name)
        comment = 'Object exists:'
    else:
        # 1504 = VM
        # unable to add actual NULL asset tag with AddObject
        #objid = rt.AddObject(name, 1504, 'NULL', name)
        objsql = "INSERT INTO Object (name,objtype_id,label) VALUES ('%s', %d, '%s')" % (name, 1504, name)
        rt.db_insert(objsql)
        objid = rt.GetObjectId(name)

        rt.InsertLog(objid, 'Object created during SaltStack automation run')

        log.debug('Configuring interfaces: %s' % str(interfaces))
        for interface, ifconfig in interfaces.items():
            mac = ifconfig['mac']
            bridge = ifconfig['bridge']
            ip4 = ifconfig.get('ip4', None)
            ip6 = ifconfig.get('ip6', None)
            portlabel = name[:8] + '_' + ifconfig['bridge'][:4]

            rt.InterfaceAddIpv4IP(objid, interface, ip4)
            rt.SetIPName(objid, ip4)
            if ip6 != None:
                rt.InterfaceAddIpv6IP(objid, interface, ip6)
                #broken, "Column 'ip' cannot be null
                #rt.SetIPName(objid, ip6)

            # 24 = 1000Base-T
            # Q: what is iif_id ?
            portsql = "INSERT INTO Port (object_id, name, iif_id, type, l2address, label) VALUES (%d, '%s', 1, 24, '%s', '%s')" % (objid, interface, mac.replace(':', '').upper(), portlabel)
            rt.db_insert(portsql)

        # 11 = Server, 32 = Nuremberg, 34 = Prague, 44 = Production, 48 = Testing
        tagmap = {'Nuremberg': 32, 'Prague': 34, 'Production': 44, 'Testing': 48}
        tags = [11]
        if city in tagmap:
            tags.append(tagmap[city])
        if usage in tagmap:
            tags.append(tagmap[usage])
        for tagid in tags:
            tagsql = "INSERT INTO TagStorage (entity_realm, entity_id, tag_id, user, date) VALUES ('object', %d, %d, '%s', now())" % (objid, tagid, 'SaltStack Automation User')
            rt.db_insert(tagsql)

        comment = 'Object created:'

    if objid:
        url='https://racktables.suse.de/index.php?page=object&tab=default&object_id=' + str(objid)
        ret['comment'] = comment + ' ' + url
    else:
        ret['comment'] = 'RackTables object creation failed'
        ret['result'] = False
    return(ret)
