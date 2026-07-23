{%- from 'infrastructure/salt/map.jinja' import git -%}

salt_pistis_package:
  pkg.installed:
    - name: pistis

salt_pistis_files:
  file.managed:
    - names:
        - /etc/systemd/system/salt-stage.path:
            - source: salt://infrastructure/salt/files/etc/systemd/system/salt-stage.path
            - mode: '0644'
        - /etc/systemd/system/salt-stage.service:
            - source: salt://infrastructure/salt/files/etc/systemd/system/salt-stage.service
            - mode: '0644'
        - /etc/pistis:
            - contents:
                - {{ pillar.get('managed_by_salt_formula', '# Managed by the infrastructure formula') | yaml_encode }}
                - 'GITLAB_TOKEN={{ salt['pillar.get']('infrastructure:salt:pistis:gitlab_token', '') }}'
            - mode: '0600'
    - context:
        branch: {{ git.branch }}
        directory: {{ git.directory }}
    - template: jinja

salt_pistis_service:
  service.running:
    - name: salt-stage.path
    - reload: False
    - watch:
        - file: salt_pistis_files
