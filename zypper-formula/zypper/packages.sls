{%- set packages = salt['pillar.get']('zypper:packages', {}) %}
{%- set defaults = namespace(refresh=False) %}
{%- set fromdefaults = [] %}
{%- set fromrepos = {} %}

{%- for package, config in packages.items() %}

{%- if 'fromrepo' in config -%}
{%- set refresh = config.get('refresh', False) -%}
{%- do fromrepos.update({ package: {'fromrepo': config.fromrepo, 'refresh': refresh} }) %}
{%- else %}

{%- if 'refresh' in config and config.refresh -%}
{%- set defaults.refresh = True -%}
{%- endif %}
{%- do fromdefaults.append(package) %}
{%- endif %}

{%- endfor %}

{%- if fromdefaults | length %}
zypper_packages:
  pkg.installed:
    - pkgs:
      {%- for package in fromdefaults %}
      - {{ package }}
      {%- endfor %}
    {%- if defaults.refresh %}
    - refresh: True
    {%- endif %}
{%- endif %}

{%- if fromrepos | length %}
{%- for package, data in fromrepos.items() %}
zypper_pkg_{{ package }}:
  pkg.installed:
    - name: {{ package }}
    {%- if 'refresh' in data %}
    - refresh: {{ data.refresh }}
    {%- endif %}
    {%- if 'fromrepo' in data %}
    - fromrepo: {{ data.fromrepo }}
    {%- endif %}
{%- endfor %}
{%- endif %}
