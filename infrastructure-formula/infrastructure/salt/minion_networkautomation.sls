{%- set highpillar = salt['pillar.get']('infrastructure:salt', {}) -%}
{%- set mypillar = highpillar.get('odd_proxy', {}) -%}

{%- if mypillar %}
include:
  - .proxy_networkautomation

salt_odd_proxy_config:
  file.managed:
    - names:
      - /etc/salt-pod/minion:
        - contents: |
            # Managed by Salt
            {%- if 'master' in mypillar %}
            master:
              {%- for master in mypillar['master'] %}
              - {{ master }}
              {%- endfor %}
            {%- endif %}
            log_level: info
            saltenv: {{ highpillar.get('saltenv', 'production_network') }}
            grains:
              odd_lobster: true
              {%- if 'domain' in mypillar %}
              domain: {{ mypillar['domain'] }}
              {%- endif %}
      - /etc/salt-pod/minion_schedule.conf:
        - source: salt://{{ slspath }}/files/etc/salt/schedule.conf.j2
        - template: jinja
    {%- if 'minions' in mypillar %}
    - watch_in:
    {%- for minion in mypillar['minions'] %}
      - user_service: Container {{ minion }} is running
      - podman: Container {{ minion }} is present
    {%- endfor %}
    {%- endif %}
    - require:
      - file: salt_pod_dirs

{%- else %}
salt_odd_proxy_fail:
  test.fail_without_changes:
    - name: infrastructure:salt:odd_proxy pillar is empty, refusing to configure
{%- endif %} {#- close pillar check -#}
