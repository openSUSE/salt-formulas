{%- from 'infrastructure/salt/map.jinja' import git, formulas -%}

salt_git_user:
  user.present:
    - name: {{ git.user }}
    - usergroup: false
    - fullname: Git Cloney
    - system: true
    - home: /var/lib/{{ git.user }}
    - createhome: false
    - shell: /sbin/nologin

salt_git_directory:
  file.directory:
    - names:
        - {{ git.directory }}
        {%- if 'repository' in formulas %}
        - {{ formulas.directory }}
        {%- endif %}
    - user: {{ git.user }}
    - group: salt
    - require:
        - user: salt_git_user
    {%- if 'repository' in formulas %}
    - require_in:
        - git: salt_formula_clone
    {%- endif %}

{%- for l in ['salt', 'pillar'] %}
salt_git_link_{{ l }}:
  file.symlink:
    - name: /srv/{{ l }}
    - target: {{ git.directory }}/{{ l }}
    - force: true
    - require:
        - file: salt_git_directory
{%- endfor %}

include:
  - .formulas
