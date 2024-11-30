posix1e_packages:
  pkg.installed:
    - pkgs:
        {#- the zypper pkg modules fail to resolve capabilities, in our Salt we have a custom grain to work around this limitation #}
        {%- if grains['osfullname'] != 'Leap' and 'system_python' in grains %}
        - {{ grains['system_python'] }}-pyacl
        {#- needs to be kept up to date if the system interpreter changes on Tumbleweed .. #}
        {%- elif grains['osfullname'] == 'openSUSE Tumbleweed' %}
        - python311-pyacl
        {#- Leap #}
        {%- else %}
        - python3-pyacl
        {%- endif %}
    - reload_modules: True

{%- set mypillar = pillar.get('acl', {}) %}
{%- if mypillar %}
posix1e_acls:
  posix1e_acl.present:
    - names:
        {%- for path, aclmap in mypillar.items() %}
          {%- for acl_type in ['user', 'group'] %}
            {%- if acl_type in aclmap %}
              {%- for acl_name, permissions in aclmap[acl_type].items() %}
        - {{ path }}_{{ acl_type }}_{{ acl_name }}:
            - acl_type: {{ acl_type }}
            - acl_name: {{ acl_name }}
            - permissions: {{ permissions }}
            - path: {{ path }}
              {%- endfor %} {#- close aclmap loop #}
            {%- endif %} {#- close acl_type check #}
          {%- endfor %} {#- close acl_type loop #}
        {%- endfor %} {#- close pillar loop #}
{%- endif %} {#- close pillar check #}
