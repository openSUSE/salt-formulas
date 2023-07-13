proxy:
  proxytype: napalm
  driver: junos
  host: %%DEVICE%%
  username: vrnetlab
  passwd: VR-netlab9

juniper_junos:
  # ! ports_not_delete:fxp0 is needed to prevent Salt from being disconnected during a state.apply
  ports_not_delete:
    - fxp0
  ignore_interfaces:
    - ge-0/0/9
  lacp:
    ge-0/0/7:
      description: Sample trunk on port 7
      parent: ae1
    ge-0/0/8:
      description: Sample trunk on port 8
      parent: ae1
  ntp_servers: []
  ports:
    ae1:
      description: Sample aggregated port group
      iface: ae1
      lacp_options:
        admin-key: 20
        mode: active
        period: slow
#        system-id: '00:00:00:00:00:00'
# cannot be tested in vSRX :-(
#      mclag_options:
#        chassis-id: 0
#        enabled: true
#        mc-ae-id: 1
#        redundancy-group: 1
#        status-control: active
      tagged:
      - 10
      untagged: null
  snmp: []
  syslog_servers: []
  vlans:
  - description: Sample VLAN
    id: 10
    name: vlan10
