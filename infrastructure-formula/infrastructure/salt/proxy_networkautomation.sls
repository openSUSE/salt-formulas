{%- set highpillar = salt['pillar.get']('infrastructure:salt', {}) -%}
{%- set mypillar = highpillar.get('proxy', {}) -%}

{%- if mypillar %}
include:
  - .podman

salt_pod_dirs:
  file.directory:
    - makedirs: True
    - user: root
    - group: autopod
    - mode: '0750'
    - names:
      - /etc/salt-pod/pki/minion
      - /etc/salt-pod/pki/proxy
      - /etc/salt-pod/proxy.d
    - require:
      - user: salt_pod_user

salt_podpki_files:
  file.managed:
    - user: root
    - group: autopod
    - names:
      {%- for mode in ['minion', 'proxy'] %}
      - /etc/salt-pod/pki/{{ mode }}/minion_master.pub:
        - contents_pillar: 'infrastructure:salt:proxy:podpki:master'
        - mode: '0644'
      - /etc/salt-pod/pki/{{ mode }}/minion.pub:
        - contents_pillar: 'infrastructure:salt:proxy:podpki:crt'
        - mode: '0644'
      - /etc/salt-pod/pki/{{ mode }}/minion.pem:
        - contents_pillar: 'infrastructure:salt:proxy:podpki:key'
        - mode: '0440'
      {%- endfor %}
      - /etc/motd:
        - contents:
          - This machine runs multiple Salt minion and proxy instances in individual containers.
          - Use `systemctl -Mautopod@ --user <start|stop|restart|status> [pattern]` to manage containers.
          - Use `journalctl [-t pattern]` to inspect container logs.
          - Do not modify Podman containers under the autopod@ user manually, they are managed by Salt.
    - require:
      - salt_pod_user
      - file: salt_pod_dirs

salt_pod_proxy_config:
  file.managed:
    - names:
      - /etc/salt-pod/proxy:
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
              lobster: true
              {%- if 'domain' in mypillar %}
              domain: {{ mypillar['domain'] }}
              {%- endif %}
              {%- if 'site' in mypillar %}
              site: {{ mypillar['site'] }}
              {%- endif %}
      - /etc/salt-pod/proxy_schedule.conf:
        - source: salt://{{ slspath }}/files/etc/salt/schedule.conf.j2
        - template: jinja
        - context:
            proxy: True
    {%- if 'minions' in mypillar %}
    - watch_in:
    {%- for minion in mypillar['minions'] %}
      - user_service: {{ minion }}
      - podman: Container {{ minion }} is present
    {%- endfor %}
    {%- endif %}
    - require:
      - file: salt_pod_dirs

{%- if 'minions' in mypillar %}
{%- for minion in mypillar['minions'] %}
salt_proxy_config_dir_{{ minion }}:
  file.directory:
    - name: /etc/salt-pod/proxy.d/{{ minion }}
    - require:
      - file: salt_pod_dirs

salt_proxy_config_{{ minion }}:
  file.symlink:
    - name: /etc/salt-pod/proxy.d/{{ minion }}/_schedule.conf
    - target: /etc/salt/proxy_schedule.conf
    - require:
      - file: salt_pod_dirs
      - file: salt_proxy_config_dir_{{ minion }}
    {%- if 'minions' in mypillar %}
    - watch_in:
    {%- for minion in mypillar['minions'] %}
      - user_service: {{ minion }}
      - podman: Container {{ minion }} is present
    {%- endfor %}
    {%- endif %}

{%- endfor %}
{%- endif %}

salt_proxy_scripts:
  file.managed:
    - name: /usr/local/sbin/reset-proxy-containers.sh
    - source: salt://{{ slspath }}/files/usr/local/sbin/reset-proxy-containers.sh
    - mode: '0750'

{%- else %}
salt_proxy_nw_autom_fail:
  test.fail_without_changes:
    - name: infrastructure:salt:proxy pillar is empty, refusing to configure
{%- endif %} {#- close pillar check -#}
