mine_functions:
  network.get_hostname: []

suse_ha:
  cluster:
    name: scullery
    ip_version: ipv4
    nodeid: {{ salt['grains.get']('id')[-1] | int + 1 }}
  cluster_secret: !!binary |
    LGljyn1fBRRcxLxFEgOmhILNTFY/13Cn3EwqqaBN6ynrX6flhiGyTjfW8eAQ1zlJex3uO9kssIcANw9uXLLpOCJ/Fvia3yzHNzCIxfW0zayUOBSMypN1TMKjad5/n8frAFZWNBhTcbk1Cwi764yBj8ErhsPh264qEreRzznJFGI=
  # FIXME: test with IPv6
  multicast:
    address: 239.0.0.1
    bind_address: {{ grains['ip4_interfaces']['eth0'][0] }}
  resources_dir: /data/resources
  {%- if salt['grains.get']('test:with_fencing') == true %}
  fencing:
    {%- if salt['grains.get']('test:with_stonith') == true %}
    stonith_enable: true
    {%- endif %}
    {%- if salt['grains.get']('test:with_sbd') == true %}
    sbd:
      instances:
        minion0:
          pcmk_host_list: minion0
          pcmk_delay_base: 0
        minion1:
          pcmk_host_list: minion1
          pcmk_delay_base: 0
        dynamic:
          pcmk_delay_max: 5
      devices:
        - /dev/sda
        - /dev/sdb
        - /dev/sdc
    {%- endif %}
    {%- if salt['grains.get']('test:with_ipmi') == true %}
    ipmi:
      {%- if salt['grains.get']('test:with_ipmi_custom') == true %}
      primitive:
        operations:
          start:
            timeout: 30
      {%- endif %}
      hosts:
        {%- for i in [0, 1] %}
        dev-ipmi{{ i }}:
          ip: 192.168.120.1
          port: 6001{{ i }}
          user: admin
          interface: lanplus
          priv: ADMINISTRATOR
          secret: password
        {%- endfor %}
    {%- endif %}
  {%- endif %}
  sysconfig:
    sbd:
      # FIXME: implement hardware/software watchdog support in the formula + test with software watchdog
      SBD_WATCHDOG_DEV: /dev/null
