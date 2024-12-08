# Python pillar helpers

A Python library to be used in `#!py` pillar SLS files. It allows for rendering of formula pillars based off data in YAML datasets.
The logic is opinionated and specific to the architecture of our code based infrastructure.

## Usage

Example pillar file `network.sls`:

```
#!py
from opensuse_infrastructure_formula.pillar import network

def run():
    return network.generate_network_pillar(
            [
                'iac_experts.example.com',
            ],
            __grains__['domain'],
            __grains__['host'],
    )
```

All modules are aimed to be named by the top level pillar they generate and contain a generation function which directly returns the relevant Python data structure.
