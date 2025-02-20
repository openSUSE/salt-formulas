salt_pod_user:
  group.present:
    - name: autopod
    - system: True
    - gid: 900

  user.present:
    - name: autopod
    - system: True
    - home: /var/lib/autopod
    - uid: 900
    - gid: 900
    - require:
      - group: autopod
    - require_in:
      - User session for autopod is initialized at boot

  cmd.run:
    - name: 'usermod --add-subuids 100000-165535 --add-subgids 100000-165535 autopod'
    - onchanges:
      - group: autopod
      - user: autopod
    - require_in:
      - User session for autopod is initialized at boot

include:
  - podman.containers
