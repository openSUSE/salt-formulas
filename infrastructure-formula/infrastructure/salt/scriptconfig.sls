{%- set file = '/etc/salt-scriptconfig' -%}
{%- set mypillar = salt['pillar.get']('infrastructure:salt:scriptconfig', {}) -%}

{%- if 'partner' in mypillar %}
{{ file }}_file:
  file.managed:
    - name: {{ file }}
    - replace: false

{{ file }}_values:
  file.keyvalue:
    - name: {{ file }}
    - append_if_not_found: true
    - key_values:
        {%- for option in ['partner', 'ssh_key'] %}
        {%- if option in mypillar %}
        {{ option }}: {{ mypillar[option] }}
        {%- endif %}
        {%- endfor %}
    - require:
      - {{ file }}_file
{%- endif %}
