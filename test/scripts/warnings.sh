#!/bin/sh
# Sets up a `salt` wrapper with no Python deprecation warnings
# This is a hack to ensure test suites assessing the stderr output of Salt produce consistent results
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

set -Ceu

if [ ! -f /usr/local/bin/salt ]
then
	sed \
		'/salt_main/a import warnings\nwarnings.filterwarnings("ignore", category=DeprecationWarning)' \
		/usr/bin/salt > /usr/local/bin/salt
fi
