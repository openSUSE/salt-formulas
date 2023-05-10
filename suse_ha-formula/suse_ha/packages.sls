{#-
Salt state file for managing SUSE HA related packages
Copyright (C) 2023 SUSE LLC <georg.pfuetzenreuter@suse.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
-#}

suse_ha_packages:
  pkg.installed:
    - pkgs:
      - chrony
      - conntrack-tools
      - corosync
      - crmsh
      - ctdb
      - fence-agents
      - ldirectord
      - pacemaker
      - python3-python-dateutil
      - resource-agents
      - virt-top

# in case we need SBD in the future, we can include this with a conditional
#- sbd
