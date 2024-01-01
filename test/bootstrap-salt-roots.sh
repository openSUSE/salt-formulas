# Helper script for installing the openSUSE Salt formulas in a Vagrant/Scullery test environment.
# Copyright (C) 2023-2024 Georg Pfuetzenreuter <mail+opensuse@georg-pfuetzenreuter.net>
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

if [ ! -d /srv/formulas ]
then
  mkdir /srv/formulas
fi
if [ ! -d /srv/pillar/samples ]
then
  mkdir /srv/pillar/samples
fi
for formula in $(find /vagrant -mindepth 1 -maxdepth 1 -type d -name '*-formula' -printf '%P\n')
do
  echo "$formula"
  fname="${formula%%-*}"
  src="/vagrant/$formula"
  src_states="$formula/$fname"
  src_formula="/vagrant/$src_states"
  src_pillar="/vagrant/$formula/pillar.example"
  src_test_pillar="/vagrant/$formula/tests/pillar.sls"
  if [ ! -d "$src_formula" ]
  then
    fname="${fname//_/-}"
    src_states="$formula/$fname"
    src_formula="/vagrant/$src_states"
  fi
  if [ ! -h "/srv/formulas/$fname" ]
  then
    ln -s "$src_formula" "/srv/formulas"
  fi
  dst_pillar="/srv/pillar/samples/$fname.sls"
  if [ -f "$src_test_pillar" ]
  then
    cp "$src_test_pillar" "$dst_pillar"
  elif [ -f "$src_pillar" ]
  then
    cp "$src_pillar" "$dst_pillar"
  fi
  dst_salt='/srv/salt'
  for mod in modules states proxy
  do
	  mod="_$mod"
	  src_mod="$src/$mod"
	  dst_mod="$dst_salt/$mod"

	  if [ ! -d "$dst_mod" ]
	  then
		mkdir "$dst_mod"
	  fi

	  if [ -d "$src_mod" ]
	  then
		echo "$fname: $mod"
		cp "$src_mod/"* "$dst_mod/"
	  fi
  done
done
tee /srv/pillar/top.sls >/dev/null <<EOF
{{ saltenv }}:
  '*':
    - full
EOF
tee /srv/pillar/full.sls >/dev/null <<EOF
include:
  - samples.*
EOF

/vagrant/test/scripts/proxy.sh
/vagrant/test/scripts/warnings.sh
