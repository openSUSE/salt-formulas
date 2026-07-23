#!/bin/sh
# Initialize virtual machines running vQFX and vSRX using vrnetlab containers
# Copyright (C) 2023-2024 SUSE LLC <georg.pfuetzenreuter@suse.com>
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

set -Ceu #x

# Git repository to fetch vrnetlab from ; to-do -> extract the needed files instead of cloning the whole tree
repository='https://github.com/tacerus/vrnetlab.git'
revision='SUSE-master'

docker pull registry.opensuse.org/isv/suseinfra/containers/containerfile/vrnetlab-base

wd="$PWD"

if [ ! -d ~/.cache ]
then
	mkdir ~/.cache
fi

pushd ~/.cache

if [ -d vrnetlab ]
then
	git --git-dir=$PWD/vrnetlab/.git pull origin "$revision"
else
	git clone --no-tags --single-branch -b "$revision" "$repository"
fi

pushd vrnetlab

# to-do -> somehow automate the fetching of these proprietary images better
images=('junos-vsrx3-x86-64-20.2R1.10.qcow2' 'vqfx-20.2R1.10-re-qemu.qcow2' 'vqfx-20.2R1-2019010209-pfe-qemu.qcow2')
for image in ${images[@]}
do
	test -f "$image" || cp "/opt/images/$image" .
done

pushd vsrx

mv ../junos-vsrx*.qcow2 .
make

popd

pushd vqfx

mv ../vqfx-*.qcow2 .
make

popd

container_srx='vsrx-device1'
container_qfx='vqfx-device1'

containers=("$container_srx" "$container_qfx")
for container in ${containers[@]}
do
	if docker ps -a --format '{{.Names}}' | grep -q "$container"
	then
		echo 'Removing existing container'
		docker stop "$container"
		docker rm -v "$container" || true
	fi
done

# to-do: map /dev/kvm instead of --privileged
# to-do: tag "latest" images and include run calls in loop above
docker_run=('docker' 'run' '-d' '--privileged' '--name')
${docker_run[@]} "$container_srx" vrnetlab/vr-vsrx:vsrx3-x86
${docker_run[@]} "$container_qfx" --device /dev/net/tun vrnetlab/vr-vqfx:20.2R1.10-re

popd >/dev/null

#echo "$address" > "$container-address"

popd >/dev/null

if echo "$wd" | grep -Fq 'formulas'
then
	if [ -f ".devices" ]
	then
		echo 'Existing address file, overwriting'
		rm ".devices"
	fi
	for container in ${containers[@]}
	do
		address="$(docker inspect -f '{{ range.NetworkSettings.Networks }}{{ .IPAddress }}{{ end }}' $container)"
		if [ -z "$address" ]
		then
			echo 'Failed to fetch container address, aborting.'
			exit 1
		fi

		echo "$container $address" >> ".devices"
	done
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
