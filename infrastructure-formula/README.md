# Infrastructure Salt states

The states in this directory extend other formulas using the `infrastructure` pillar.

The code under this directory is highly opinionated and specific to our infrastructure.

## Available states

### Libvirt:

`infrastructure.libvirt.domains`

Writes virtual machine domain definitions.

### SUSE HA:

`infrastructure.suse_ha.resources`

Configures virtual machine cluster resources.

### Salt:

The Salt states depend on the [Salt formula](https://github.com/saltstack-formulas/salt-formula) and a modified version of the [Podman formula](https://github.com/lkubb/salt-podman-formula). The latter is yet to be upstreamed.

`infrastructure.salt.master`

Configure a Salt master.

`infrastructure.salt.syndic`

Configure a Salt Syndic, which includes a Salt master.

`infrastructure.salt.minion`

Configures a Salt Minion.

`infrastructure.salt.proxy_master`

Extends a Salt Master with capabilities to manage proxy minions.

`infrastructure.salt.proxy_networkautomation`

Configures a container host to run Salt Proxy minions.

`infrastructure.salt.minion_networkautomation`

Extends a container host running Salt Proxy minions to run regular Salt Minions.
This is for managing devices using Salt states not implementing Salt Proxy operation and instead rely on modules on a regular minion to forward requests to an API.

`infrastructure.salt.scriptconfig`

Writes configuration used by Salt related scripts, currently only `salt-keydiff`.
