# Salt states for bootloader configuration

## Available states

`bootloader`

Runs both of the below.

`bootloader.bootloader`

Configures general settings (`/etc/sysconfig/bootloader`).

Unless disabled, changes will trigger a bootloader re-installation.

`bootloader.grub`

Configures GRUB specific settings (`/etc/default/grub`).

Unless disabled, changes will trigger the generation of a new GRUB configuration file.
