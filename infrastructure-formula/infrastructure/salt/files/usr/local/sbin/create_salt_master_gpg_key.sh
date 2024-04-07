#!/usr/bin/bash
# Script to create a private GPG key for use with Salt
# Copyright (C) 2023-2024 SUSE LLC <ignacio.torres@suse.com>
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

set -eu

mail="salt@${HOSTNAME}"
name="${HOSTNAME} (Salt Master Key)"
homedir="/etc/salt/gpgkeys"

help() {
    echo "Generate a gpg secret key in a salt master (syndic)."
    echo
    echo "Options:"
    echo "-m       email address to identify key (default: $mail)"
    echo "-n       name associated to the key (default: $name)"
    echo "-d       GPG homedir (default: $homedir)"
}

while getopts :d:m:n:h arg; do
    case ${arg} in
    d) homedir="${OPTARG}" ;;
    m) mail="${OPTARG}" ;;
    n) name="${OPTARG}" ;;
    h) help && exit ;;
    *) help && exit 1 ;;
    esac
done

if [ ! -d "$homedir" ]; then
    mkdir -p "$homedir" && chown salt:salt "$homedir" && chmod 700 "$homedir"
fi

if sudo -u salt gpg2 --batch --homedir "$homedir" -k "$mail" >/dev/null; then
    echo "A key for $mail already exists in $homedir. Aborting."
    exit 1
fi

# cleanup gpg-agent
# We need the || true in case there are no processes. Check pgrep(1).
sudo -u salt pkill gpg-agent || true

sudo -u salt gpg2 --homedir "$homedir" --batch --passphrase '' --quick-generate-key "$name <$mail>" ed25519 cert 2y
fingerprint=$(sudo -u salt gpg2 --batch --homedir "$homedir" --list-options show-only-fpr-mbox --list-secret-keys | awk '{print $1}')
sudo -u salt gpg2 --homedir "$homedir" --batch --passphrase '' --quick-add-key "$fingerprint" cv25519 encrypt 2y

set -x
sudo -u salt gpg2 --batch --homedir "$homedir" --list-keys --keyid-format 0xlong
sudo -u salt gpg2 --batch --homedir "$homedir" --export --armor "$fingerprint"
