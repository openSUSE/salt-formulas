# Salt states for Kanidm

This formula provides states for the configuration of [Kanidm](https://kanidm.com/).

## Available states

`kanidm.client`

Installs and configures the [client tools](https://kanidm.github.io/kanidm/stable/client_tools.html).

`kanidm.unixd`

Installs and configures the [UNIX daemon](https://kanidm.github.io/kanidm/stable/integrations/pam_and_nsswitch.html)
and configures nsswitch/PAM to make use of it.

`kanidm.server`

Installs and configures the server (TODO).
