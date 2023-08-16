{%- set extrascriptdir = '/usr/local/sbin/' -%}
{%- set extrascripts = ['state-apply-super-async.sh'] -%}
{%- set extrapackages = ['salt-keydiff'] -%}
{%- set formula_packages = salt['pillar.get']('profile:salt:formulas') -%}
{%- for formula in formula_packages -%}
{%- do extrapackages.append(formula ~ '-formula') -%}
{%- endfor -%}

include:
  - .common
  - salt.master

/usr/local/sbin/saltmaster-deploy:
  file.managed:
    - source: salt://profile/salt/files/usr/local/sbin/saltmaster-deploy.j2
    - template: jinja
    - mode: '0700'

salt_master_extra_scripts:
  file.managed:
    - mode: '0755'
    - names:
{%- for file in extrascripts %}
      - {{ extrascriptdir }}{{ file }}:
        - source: salt://profile/salt/files{{ extrascriptdir }}{{ file }}
{%- endfor %}

salt_master_extra_packages:
  pkg.installed:
    - names:
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
    - source: salt://profile/salt/files/srv/reactor
    - template: jinja
