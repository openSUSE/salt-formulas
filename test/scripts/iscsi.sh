#!/bin/sh
set -Ceux
if test -f /var/adm/iscsi.configured ; then exit ; fi
echo 'iqn.1996-04.de.suse:01:3d33457f6212' >| /etc/iscsi/initiatorname.iscsi
targetctl restore /vagrant/test/configs/target.json
mkdir /data/lun
targetcli <<EOS
cd /backstores/fileio
create size=5M name=data1 file_or_dev=/data/lun/1
create size=5M name=data2 file_or_dev=/data/lun/2
create size=5M name=data3 file_or_dev=/data/lun/3
cd /iscsi/iqn.2003-01.org.linux-iscsi.scullery-master0.x8664:sn.5034edf18f27/tpg1/luns
create lun=1 storage_object=/backstores/fileio/data1
create lun=2 storage_object=/backstores/fileio/data2
create lun=3 storage_object=/backstores/fileio/data3
cd /
exit
EOS
touch /var/adm/iscsi.configured
systemctl enable --now target
