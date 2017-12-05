{% set packages = salt['pillar.get']('zypper:packages', {}) %}

{% for package, data in packages.items() %}
zypper_pkg_{{ package }}:
  pkg.installed:
    - name: {{ package }}
    {% if 'refresh' in data %}
    - refresh: {{ data.refresh }}
    {% else %}
    - refresh: True
    {% endif %}
    {% if 'fromrepo' in data %}
    - fromrepo: {{ data.fromrepo }}
    {% endif %}
{% endfor %}
