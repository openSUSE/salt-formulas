#!/bin/sh
# Initialize a virtual machine running vSRX using a vrnetlab container
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

set -Ceux

# Git repository to fetch vrnetlab from ; to-do -> extract the needed files instead of cloning the whole tree
repository='https://github.com/tacerus/vrnetlab.git'
revision='vsrx2'

# to-do: docker setup is somewhat out of scope
SUDO=''
command -v sudo && SUDO=sudo
rpm -q docker >/dev/null || $SUDO zypper -n in docker
systemctl is-active docker || $SUDO systemctl enable --now docker
if getent passwd geeko >/dev/null
then
	if ! groups geeko | grep -q docker
	then
		$SUDO usermod -aG docker geeko
		if [ "$USER" == 'geeko' ]
		then
			newgrp docker
		fi
	fi
fi

docker pull registry.opensuse.org/isv/suseinfra/containers/containerfile/vrnetlab-base

wd="$PWD"
pushd /tmp

if [ -d vrnetlab ]
then
	git --git-dir=$PWD/vrnetlab/.git pull origin "$revision"
else
	git clone --no-tags --single-branch -b "$revision" "$repository"
fi

pushd vrnetlab/vsrx

# to-do -> somehow automate the fetching of this proprietary image better
image='junos-vsrx3-x86-64-20.2R1.10.qcow2'
test -f "$image" || cp "/opt/images/$image" .

make

container='vsrx-device1'
if docker ps -a --format '{{.Names}}' | grep -q "$container"
then
	echo 'Removing existing container'
	docker stop "$container"
	docker rm -v "$container" || true
fi

# to-do: map /dev/kvm instead of --privileged
docker run -d --privileged --name "$container" vrnetlab/vr-vsrx:vsrx3-x86

popd >/dev/null

address="$(docker inspect -f '{{ range.NetworkSettings.Networks }}{{ .IPAddress }}{{ end }}' $container)"
if [ -z "$address" ]
then
	echo 'Failed to fetch container address, aborting.'
	exit 1
fi
#echo "$address" > "$container-address"

popd >/dev/null

if echo "$wd" | grep -Fq 'formulas'
then
	if [ -f ".$container-address" ]
	then
		echo 'Existing address file, overwriting'
		rm ".$container-address"
	fi
	echo "$address" > ".$container-address"
fi

#if ! grep -Fqx "$address $container" /etc/hosts
#then
#	if grep -Fq "$container" /etc/hosts
#	then
#		sed -Ei "s/^.*$container.*$/$address $container/" /etc/hosts
#	else
#		echo "$address $container" >> /etc/hosts
#	fi
#fi
