{%- set deploy_password = salt['pillar.get']('infrastructure:salt:reactor:update_fileserver_deploy_password', '') -%}
{%- raw -%}
{%- if data.data == "{% endraw %}{{ deploy_password }}{% raw %}" -%}
{%- endraw %}
update_fileserver:
  runner.fileserver.update: []
  runner.git_pillar.update: []
{%- if grains['domain'] == 'infra.opensuse.org' %} {#- to-do: find a common solution #}
update_fileserver_ng:
  local.state.apply:
    - tgt: minnie.infra.opensuse.org
    - args:
      - mods: profile.salt.git.base
{%- endif -%}
{%- raw %}
{%- endif -%}
{%- endraw -%}
