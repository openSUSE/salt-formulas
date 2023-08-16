{%- set mypillar        = salt['pillar.get']('infrastructure:salt:reactor', {})            -%}
{%- set target          = mypillar.get('update_fileserver_ng', {}).get('target')           -%}
{%- set deploy_password = mypillar.get('update_fileserver', {}).get('deploy_password', '') -%}
{%- raw -%}
{%- if data.data == "{% endraw %}{{ deploy_password }}{% raw %}" -%}
{%- endraw %}
update_fileserver:
  runner.fileserver.update: []
  runner.git_pillar.update: []
{%- if target %}
update_fileserver_ng:
  local.state.apply:
    - tgt: {{ target }}
    - args:
      - mods: profile.salt.git.base
{%- endif -%}
{%- raw %}
{%- endif -%}
{%- endraw -%}
