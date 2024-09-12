{%- from 'nftables/map.jinja' import nft, dir %}

#nftables_packages:
#  pkg.installed:
#    - pkgs:
#      - nftables-service

nftables_directory:
  file.directory:
    - names:
        - {{ dir }}/active
        - {{ dir }}/passive
    - makedirs: true

nftables_config_base:
  file.managed:
    - name: /etc/nftables.conf
    - contents: |
        #!/usr/sbin/nft -f
        include "{{ dir }}/active/*.conf"

{%- for category, config in nft.items() %}

nftables_config_{{ category }}:
  file.managed:
    - name:
    {%- set file = category ~ '.conf' -%}
    {%- if 'priority' in config -%}
    {%- set file = config['priority'] ~ '_' ~ file -%}
    {%- endif -%}
    {{ ' ' ~ dir }}/{{ config.get('mode', 'active') }}/{{ file }}
    - template: jinja
    - source: salt://{{ slspath }}/files/nftables.j2
    - context:
        config: {{ config }}
{%- endfor %}
