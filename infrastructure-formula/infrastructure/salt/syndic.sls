include:
  - salt.gitfs.pygit2
  - salt.syndic
  - .master

{%- set id = grains['id'] %}
{%- set gpg_script = '/usr/local/sbin/create_salt_master_gpg_key.sh' %}

install_gpg_bootstrap_script:
  file.managed:
    - name: {{ gpg_script }}
    - source: salt://{{ slspath }}/files{{ gpg_script }}
    - mode: '0750'

run_gpg_bootstrap_script:
  cmd.run:
    - name: {{ gpg_script }} -m salt@{{ id }} -n '{{ id }} (Salt Master Key)'
    - unless: gpg2 --homedir /etc/salt/gpgkeys -k salt@{{ id }} 1>/dev/null 2>/dev/null
    - require:
      - file: install_gpg_bootstrap_script

/etc/salt/gpgkeys:
  file.directory:
    - user: salt
    - group: salt
    - dir_mode: '0700'
    - file_mode: '0600'
    - recurse:
        - user
        - group
        - mode
    - watch:
      - cmd: run_gpg_bootstrap_script
