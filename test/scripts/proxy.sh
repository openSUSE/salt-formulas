#!/bin/sh
# Initializes a Salt proxy for testing formulas on network devices
# Copyright (C) 2023 SUSE LLC <georg.pfuetzenreuter@suse.com>
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

set -Ceu

proxyp='salt-proxy'
rpm -q "$proxyp" >/dev/null || zypper -n in "$proxyp"

proxyc='/etc/salt/proxy'
tee "$proxyc" >/dev/null <<EOF
master: 127.0.0.1
log_level: debug
EOF

proxyf='/etc/salt/proxy_schedule'
tee "$proxyf" >/dev/null <<EOF
schedule:
  __mine_interval: {enabled: true, function: mine.update, jid_include: true, maxrunning: 2,
    minutes: 60, return_job: false, run_on_start: true}
  __proxy_keepalive:
    enabled: true
    function: status.proxy_reconnect
    jid_include: true
    kwargs: {proxy_name: napalm}
    maxrunning: 1
    minutes: 1
    return_job: false
  enabled: true
EOF

proxyd='/etc/salt/proxy.d/vsrx-device1'
test -d "$proxyd" || mkdir -p "$proxyd"

proxyl="$proxyd/_schedule.conf"
test -L "$proxyl" || ln -s "$proxyf" "$proxyl"

# to-do: scan for multiple devices
af='/vagrant/.devices'
if [ -f "$af" ]
then
	dp='/srv/pillar/devices'
	if [ ! -d "$dp" ]
	then
		mkdir "$dp"
	fi
	while read -r device address
	do
		if [ -f "$dp/$device.sls" ]
		then
			rm "$dp/$device.sls"
		fi
		printf 'proxy:\n  host: %s\n' "$address" > "$dp/$device.sls"
		systemctl enable --now "salt-proxy@$device"
	done < "$af"
else
	echo 'No devices'
fi

