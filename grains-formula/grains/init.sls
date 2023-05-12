/etc/salt/grains:
  file.managed:
    - source:
        - salt://grains/files/grains
    - user: root
    - group: root
    - mode: '0644'
    - template: jinja
