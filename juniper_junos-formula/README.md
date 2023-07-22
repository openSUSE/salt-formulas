# Salt states for Juniper Junos

This formula helps with configuring Juniper network devices using Salt pillars.

## Disclaimer

This formula is yet to be fully tested and hence considered a work in progress project. There are various "FIXME" remarks around the files which are intended to be revisited over time.

## Available states

`juniper_junos.firewall`

Manages a Juniper firewall configuration. Intended for use with Juniper SRX firewalls.

`juniper_junos.switch`

Manages a Juniper switch configuration. Intended for use with Juniper QFX switches, but can also be applied on SRX devices.

## History

This Salt formula was created in an effort to automate the network infrastructure in the SUSE datacenters.
The modules and conversion scripts have originally been developed for SUSE by DEVOQ TECHNOLOGY I.K.E. as part of a contracted network automation project before they were refactored and integrated with our formula ecosystem.

## Testing

The test suite currently only validates whether the configuration is applied as expected from the Salt end and does not assess the expected functionality of the network device. More importantly, the test pillar still needs to be expanded to cover the complete templating logic.

To run the test suite, a lab environment can be set up if the proprietary vSRX and vQFX images are provided in `/opt/images`.

#### Test dependencies

- Docker
- Libvirt + QEMU
- Scullery
- Pytest + Testinfra

Generally only Pytest and Testinfra are required, the other tools are helpers for setting up the needed environment. The Pytest suite expects a network device with the default vrnetlab admin credentials to be accessible at the address passed as `--target`. The minions in Salt should be called `vqfx-device1` and `vsrx-device1` respectively, as the `--model` argument will map `qfx` and `srx` to them.

#### Test steps

1. `juniper_junos-formula/bin/lab.sh` - this clones a forked vrnetlab repository, pulls our vrnetlab-base container image, re-builds it using the proprietary images, and runs the containers - these containers in return run the needed virtual machines and are hence started with additional privileges

2. `scullery --config test/scullery.ini --suite juniper_junos_formula.tumbleweed.one_master --env` - this instantiates a virtual machine running the Salt master and proxy minions

3. `pytest --disable-warnings -v -rx --hosts scullery-master0 --ssh-config .scullery_ssh --sudo --model=<model> --target=<target> juniper_junos-formula/tests/` - use your favourite arguments to customize the Pytest run, replace `<model>` with either `qfx` or `srx`, and `<target>` with the respective container address found in the `.devices` file created by `lab.sh`
