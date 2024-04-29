#!/bin/sh -Cefu
# This compiles the modules shipped on an openSUSE system into a JSON file,
# which is then used by the formula to differentiate between modules requiring package
# installation and ones bundled with the core apache2 packages.
# Should be run on a machine which does NOT have any additional apache2-mod_* package installed.
#
# Copyright (C) 2024 Georg Pfuetzenreuter <mail+opensuse@georg-pfuetzenreuter.net>
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

# Check if a usable apache2 is installed
libdir='/usr/lib64/apache2/'
if [ ! -d "$libdir" ]
then
  echo 'Missing libdir.'
  exit 1
fi

# Define output directory - if not run in the salt-formulas.git root, OUTDIR can be specified
outdir="${OUTDIR?:apache_httpd-formula/apache_httpd/modules/os}"
if [ ! -d "$outdir" ]
then
  echo 'Missing output directory.'
  exit 1
fi

# Define output file name - if OS is not specified, the current OS name converted into the "oscodename" grain format will be used
set +u
if [ -z "$OS" ]
then
  . /etc/os-release
  OS="${PRETTY_NAME// /_}"
fi
set -u
outfile="$outdir/$OS.json"

# Start JSON file with "base" section
printf '{\n    "base": [\n' >| "$outfile"

# Gather installed modules
find "$libdir" \
  -name 'mod_*.so' -type f \
  -execdir basename {} \; \
    | LC_ALL=C sort \
    | sed -E \
        -e 's/mod_([a-z0-9_]+)\.so/        "\1"/' \
        -e '$ ! s/$/,/' \
      >> "$outfile"

# End "base" and start "default" section
printf '    ],\n    "default": [\n' >> "$outfile"

# Gather modules enabled by default
awk -F= \
  '/^APACHE_MODULES=".*"$/{ gsub("\"", "", $2) ; gsub(" ", "\",\n        \"", $2) ; print "        \"" $2 "\"" }' \
  /usr/share/fillup-templates/sysconfig.apache2 \
  >> "$outfile"

# End JSON file
printf '    ]\n}\n' >> "$outfile"
