{%- set mypillar  = salt['pillar.get']('zypper:variables', {}) %}
{%- set directory = '/etc/zypp/vars.d/' %}

zypp_variables_directory:
  file.directory:
    - name: {{ directory }}
    - clean: true

{%- if mypillar %}
zypp_variables:
  file.managed:
    - names:
        {%- for key, value in mypillar.items() %}
        - {{ directory }}{{ key }}:
            - contents:
                {#- zypp takes the first line as the value, comments can only go after #}
                - '{{ value }}'
                - {{ pillar.get('managed_by_salt_formula', '# Managed by the zypper formula') | yaml_encode }}
        {%- endfor %}
    - mode: '0644'
    - user: root
    - group: root
    - require_in:
        - file: zypp_variables_directory
{%- endif %}
