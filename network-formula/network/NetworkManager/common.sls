{%- from 'network/NetworkManager/map.jinja' import base, base_backup, script -%}

network_nm_backup_directory:
  file.directory:
    - name: {{ base_backup }}
    - mode: '0750'
    - user: root
    - group: root

network_nm_script:
  file.managed:
    - name: {{ script }}
    - source: salt://{{ slspath }}/files/saltsafe_nm
    - mode: '0750'
    - user: root
    - group: root
    - template: jinja
    - context:
        base: {{ base }}
        base_backup: {{ base_backup }}
