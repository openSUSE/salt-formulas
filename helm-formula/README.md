# Salt states for Helm

## Dependencies

This will neither work with the `helm` execution and state modules shipped with Salt core nor with the latest revision of `saltext-helm`.
It depends on a refactored version of the modules (https://github.com/salt-extensions/saltext-helm/pull/21) and `pyhelm3`.

A compatible extension package can be found in `isv:SUSEInfra:Devel`.

## Available states

`helm`

Ensures packages needed for managing Helm are installed, and ensures releases match the pillar configuration.
