{% set repositories = salt['pillar.get']('zypper:repositories', {}) %}

{% for repo, data in repositories.items() %}
{{ repo }}:
  pkgrepo.managed:
    - baseurl: {{ data.baseurl }}
    {% if data.has_key('priority') %}
    - priority: {{ data.priority }}
    {% endif %}
    {% if data.has_key('refresh') %}
    - refresh: {{ data.refresh }}
    {% endif %}
    {% if data.has_key('gpgcheck') %}
    - gpgcheck: {{ data.gpgcheck }}
    {% endif %}
    {% if data.has_key('key_url') %}
    - key_url: {{ data.key_url }}
    {% endif %}
    {% if data.has_key('gpgautoimport') %}
    - gpgautoimport: {{ data.gpgautoimport }}
    {% endif %}
{% endfor %}
