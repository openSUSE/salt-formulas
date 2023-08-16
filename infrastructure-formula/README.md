# Infrastructure Salt states

The states in this directory share the `infrastructure` pillar dictionary to configure virtual machines and virtualization clusters.

The code under this directory is highly opinionated and specific to our infrastructure.

## Available states

`infrastructure.libvirt.domains`

Writes virtual machine domain definitions.

`infrastructure.suse_ha.resources`

Configures virtual machine cluster resources.
