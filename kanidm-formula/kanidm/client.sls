kanidm_client_packages:
  pkg.installed:
    - name: kanidm-clients

kanidm_client_config_header:
  file.prepend:
    - name: /etc/kanidm/config
    - text: {{ pillar.get('managed_by_salt_formula', '# Managed by the Kanidm formula') | yaml_encode }}

kanidm_client_config:
  file.serialize:
    - name: /etc/kanidm/config
    - dataset_pillar: kanidm:client:config
    - serializer: toml
