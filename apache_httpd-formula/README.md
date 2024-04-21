# Salt states for the Apache HTTP server

## Available states

`apache_httpd`

Installs and configures `apache2`.

`apache_httpd.purge`

Removes configuration files neither managed by RPM packages, nor by Salt.
Included in `apache_httpd` by default, unless `apache_httpd:purge` is set to `False`.
