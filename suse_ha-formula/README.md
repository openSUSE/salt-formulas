# Salt states for the SUSE Linux Enterprise High Availability Extension

## Available states

`suse_ha`

- Installs and configures a HA node.

`suse_ha.corosync`

- Configures Corosync.

`suse_ha.kernel`

- Enables the kernel software watchdog.

`suse_ha.pacemaker`

- Configures Pacemaker, including:
  * IPMI fencing resources
  * STONITH

`suse_ha.packages`

- Installs HA related packages

`suse_ha.repositories`

- Configures SLES HA repositories

`suse_ha.resources`

- Configures primitive resources

`suse_ha.service`

- Enables Pacemaker (unfinished state)
