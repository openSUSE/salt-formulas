{% set packages = salt['pillar.get']('zypper:packages', {}) %}

{% for package, data in packages.iteritems() %}
{{ package }}:
  pkg.installed:
    {% if data.has_key('refresh') %}
    - refresh: {{ data.refresh }}
    {% else %}
    - refresh: True
    {% endif %}
    {% if data.has_key('fromrepo') %}
    - fromrepo: {{ data.fromrepo }}
    {% endif %}
{% endfor %}
