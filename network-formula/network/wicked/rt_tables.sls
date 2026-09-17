network_wicked_rt_tables:
  file.managed:
    - name: /etc/iproute2/rt_tables
    - source: salt://{{ slspath }}/files/etc/iproute2/rt_tables.jinja
    - mode: '0644'
    - template: jinja
    - require_in:
        - sls: network.wicked.interfaces
