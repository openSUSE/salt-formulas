{%- set mypillar = salt['pillar.get']('zypper:config', {}) %}

{%- set zypp_conf = mypillar.get('zypp_conf', {}) %}
{%- set zypper_conf = mypillar.get('zypper_conf', {}) %}

{%- if zypp_conf %}
/etc/zypp/zypp.conf:
  ini.options_present:
    - sections:
        {%- for section, data in zypp_conf.items() %}
        {{ section }}:
          {%- for config, value in data.items() %}
          {{ config }}: '{{ value }}'
          {%- endfor %}
        {%- endfor %}
{%- endif %}

{%- if zypper_conf %}
/etc/zypp/zypper.conf:
  ini.options_present:
    - sections:
        {%- for section, data in zypper_conf.items() %}
        {{ section }}:
          {%- for config, value in data.items() %}
          {{ config }}: '{{ value }}'
          {%- endfor %}
        {%- endfor %}
{%- endif %}
