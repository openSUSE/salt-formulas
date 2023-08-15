/etc/logrotate.d/salt:
  file.managed:
    - source: salt://{{ slspath }}/files/etc/logrotate.d/salt
    - user: root
    - group: root
    - mode: '0644'
