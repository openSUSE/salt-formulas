{%- set id = grains['id'] %}

include:
  - devices.{{ id }}

proxy:
  proxytype: napalm
  driver: junos
  username: vrnetlab
  passwd: VR-netlab9

juniper_junos:
  interfaces:
    ae0:
      mtu: 9100
      description: Katze
      ae:
        lacp:
          force-up: true
          system-id: ff:ff:ff:ff:ff:ff
          admin-key: 65535
    #    mc:
    #      mc-ae-id: asdf
    #      redundancy-group: bla
    #      chassis-id: 12345
    #      mode: active-active
    #      status-control: asdf
    #      init-delay-time: 300

    # reth* interfaces will be counted to set the reth-count
    ge-0/0/2:
      description: foo
      mtu: 9100
      #reth: reth0
      # cannot be combined with vlan:access, only vlan:trunk
      native_vlan: 2
      units:
        0:
          description: bar
          inet:
            addresses:
              - 192.168.99.1/32
          inet6:
            addresses:
              - fd15:5695:f4b6:43d5::1/128

    ge-0/0/3:
      mtu: 9100
      # lacp cannot be combined with any other options
      lacp: ae0

    ge-0/0/4:
      mtu: 9000
      units:
        0:
          vlan:
            # access/trunk cannot co-exist
            type: trunk
            ids:
              - 1
              - 2

  {%- if 'srx' in id %}
    reth0:
      description: test
      mtu: 9100
      redundancy-group: 1
      units:
        0:
          vlan:
            type: access
            ids:
              - 1

    ge-0/0/1:
      mtu: 9100
      reth: reth0

  redundancy_groups:
    1:
      nodes:
        1:
          priority: 10
  {%- endif %}

  vlans:
    vlan1:
      id: 1
    vlan2:
      id: 2
    vlan200:
      id: 200
      description: baz

  ignore:
    # these need to be ignored to prevent Salt from being disconnected during testing
    interfaces:
      - fxp0
      - em0
      - em1

  syslog:
    user:
      facilities:
        any: emergency

    file:
      messages:
        facilities:
          any: notice
          authorization: info
          interactive-commands: any

  {%- if 'srx' in id %}
  zones:
    myfirstzone:
      interfaces:
        ge-0/0/2:
          protocols:
            - ospf

    mysecondzone:
      interfaces:
        ge-0/0/4:
          system-services:
            - dns
            - ssh
  {%- endif %}
