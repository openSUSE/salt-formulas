{%- set domain = grains['domain'] %}
{%- set highpillar = salt['pillar.get']('infrastructure:salt', {}) -%}
{%- set proxydomain = salt['pillar.get']('infrastructure:salt:proxy_domains:' ~ domain) -%}
{%- set pkidir = '/etc/salt/pki/master/minions/' %}

{%- if proxydomain | length and 'certificate' in proxydomain and 'minions' in proxydomain %}
salt_proxy_preseed:
  file.managed:
    - user: salt
    - group: salt
    - mode: '0644'
    - names:
      {%- for minion in proxydomain['minions'] %}
      - {{ pkidir }}{{ minion }}:
        - contents: |
            {{ proxydomain['certificate'] | base64_decode | indent(12) }}
      {%- endfor %}
{%- endif %}

/srv/pillar_network/network_data/switches:
  file.directory:
    - user: {{ highpillar.get('sync_user', 'sync') }}
    - group: salt
    - makedirs: true

/srv/pillar_network/top.sls:
  file.managed:
    - group: salt
    - contents: |
        {% raw %}{{ saltenv }}{%- endraw %}:
          '*':
            - network_data
    - require:
      - file: /srv/pillar_network/network_data/switches
