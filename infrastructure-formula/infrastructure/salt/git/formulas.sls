{%- from 'infrastructure/salt/map.jinja' import git, formulas -%}

{%- if 'repository' in formulas %}
{%- set branch = formulas.get('branch', git.branch) %}

salt_formula_clone:
  git.latest:
    - name: {{ formulas['repository'] }}
    - target: {{ formulas.directory }}
    - branch: {{ branch }}
    - rev: {{ branch }}
    {#- test apply fails if the user does not yet exist #}
    {%- if not opts['test'] or salt['user.info'](git.user) %}
    - user: {{ git.user }}
    {%- endif %}
    - force_checkout: true
    - force_clone: true
    - force_reset: true
    - fetch_tags: false
    - submodules: true
{%- endif %}
