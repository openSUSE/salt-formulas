#!/bin/sh
# This creates a single async state.apply job for each given host.
# Prevents congested jobs when targeting too many hosts. If that does not convince you, it makes it easier to look up results for a specific host.
#
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

state="$1"
input="$2"
log="$(mktemp -p /tmp superasync-XXXXX)"
count=0

if [ -z "$1" ]
then
	echo 'Please specify a state to apply.'
	exit 1
fi

if [ -z "$input" ]
then
	echo 'No input file specified, reading from standard input, type "done" or press Ctrl+D when done ...'
	input='/dev/stdin'
fi

while read host
do
	if [ "$host" = 'done' ]
	then
		break
	fi
	printf 'Job for %s ...\t' "$host"
	jid="$(salt --async --out=quiet --show-jid "$host" state.apply "$state" | cut -d':' -f2)"
	count="$((count + 1))"
	echo "$jid" >> "$log"
	printf '%s\n' "$jid"
done < "$input"

sed -i -e 's/ //' "$log"

printf 'Created %s jobs, wrote JIDs to %s\n' "$count" "$log"
