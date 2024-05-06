# Salt states for SUSE backup scripts

## Available states

`backupscript`

Depending on the pillar configuration, installs and configures:

- [influxdb-backupscript](https://build.opensuse.org/package/show/home:lrupp/influxdb-backupscript)
- [mysql-backupscript](https://build.opensuse.org/package/show/home:lrupp/mysql-backupscript)
- [postgresql-backupscript](https://build.opensuse.org/package/show/home:lrupp/postgresql-backupscript)

Backupscripts which are installed but not defined in the pillar will be disabled.
