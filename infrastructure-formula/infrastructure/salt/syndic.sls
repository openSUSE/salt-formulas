include:
  - salt.gitfs.pygit2
  - salt.syndic
  - .master

salt_syndic_minion_key_permissions:
  file.managed:
    - name: /etc/salt/pki/minion/minion.pem
    - user: salt
    - mode: '0400'
    - create: false
    - replace: false
