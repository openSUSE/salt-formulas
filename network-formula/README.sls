# Salt states for managing the network

## Available states

`network`

Configures all possible aspects using either the pillar specified or the default backend (Wicked).

`network.wicked`

Configures both, interfaces and routes, using Wicked.

`network.wicked.interfaces`

Configures interfaces using Wicked.

`network.wicked.routes`

Configures routes using Wicked.

`network.wicked.netconfig`

Configures netconfig.
