#!/bin/bash
# Script to reset and update all proxy containers
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

POD_USER=autopod
UNITDIR=~autopod/.config/systemd/user

SRUN_ARGS=('--wait' '--user' "-M$POD_USER@" '-Pq')
SRUN="systemd-run ${SRUN_ARGS[@]}"

SCTL_ARGS=("-M$POD_USER@" '--user')
SCTL="systemctl ${SCTL_ARGS[@]}"


echo '==> Pulling images ...'
$SRUN sh -c 'podman images --format "{{.Repository}}" | sed "/<none>/d" | xargs podman pull -q'

echo '==> Fetching containers ...'
# https://github.com/containers/podman/issues/14888
CONTAINERS=($(printf '%s ' `$SRUN podman ps --no-trunc --format '{{.Names}}'`))

echo '==> Fetching services ...'
SERVICES=($(find "$UNITDIR" -type f -name '*.service' -printf '%P '))

if [ "${#SERVICES[@]}" -gt 0 ]
then
	echo '==> Stopping and disabling services ...'
	$SCTL disable --now ${SERVICES[@]}
fi

echo '==> Purging containers ...'
# containers should already be gracefully stopped using the systemd call above; stopping any remaining ones before removing all
$SRUN sh -c 'podman ps -aq | xargs -I ? sh -c "podman stop ? && podman rm ?" >/dev/null'

if [ "${#SERVICES[@]}" -gt 0 ]
then
	echo '==> Purging services ...'
	rm -r "$UNITDIR"/*
	$SCTL daemon-reload
	$SCTL --state not-found reset-failed
fi

echo '==> Applying highstate ...'
salt-call -lerror --state-output=mixed state.apply

echo '==> OK <=='
