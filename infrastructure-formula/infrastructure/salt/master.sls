{%- set extrascriptdir = '/usr/local/sbin/' -%}
{%- set extrascripts = ['qjid', 'state-apply-super-async.sh'] -%}
{%- set extrapackages = ['salt-keydiff'] + salt['pillar.get']('infrastructure:salt:formulas', []) -%}

include:
  - salt.master

salt_master_extra_scripts:
  file.managed:
    - names:
      - {{ extrascriptdir }}saltmaster-deploy:
        - source: salt://infrastructure/salt/files{{ extrascriptdir }}saltmaster-deploy.j2
        - template: jinja
        - mode: '0700'
{%- for file in extrascripts %}
      - {{ extrascriptdir }}{{ file }}:
        - source: salt://infrastructure/salt/files{{ extrascriptdir }}{{ file }}
        - mode: '0755'
{%- endfor %}

salt_master_extra_packages:
  pkg.installed:
    - pkgs:
{%- for package in extrapackages %}
      - {{ package }}
{%- endfor %}

/etc/salt/gpgkeys:
  file.directory:
    - user: salt
    - group: salt
    - dir_mode: '0700'
    - file_mode: '0600'
    - recurse:
        - user
        - group
        - mode

/srv/reactor:
  file.recurse:
    - source: salt://infrastructure/salt/files/srv/reactor
    - template: jinja

{%- if salt['pillar.get']('infrastructure:salt:master:git_gc', False) %}
salt_git_gc:
  file.managed:
    - names:
    {%- for suffix in ['timer', 'service'] %}
    {%- set unit = '/etc/systemd/system/salt-git-gc.' ~ suffix %}
      - {{ unit }}:
        - source: salt://{{ slspath }}/files/{{ unit }}
    {%- endfor %}
  service.running:
    - name: salt-git-gc.timer
    - enable: true
{%- endif %}
