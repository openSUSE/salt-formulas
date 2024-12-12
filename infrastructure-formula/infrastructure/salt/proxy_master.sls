{%- set domain = grains['domain'] %}
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
