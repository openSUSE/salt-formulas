{% set repositories = salt['pillar.get']('zypper:repositories', {}) %}

{% for repo, data in repositories.items() %}
{{ repo }}:
  pkgrepo.managed:
    - baseurl: {{ data.baseurl }}
    {% if 'priority' in data %}
    - priority: {{ data.priority }}
    {% endif %}
    {% if 'refresh' in data %}
    - refresh: {{ data.refresh }}
    {% endif %}
    {% if 'gpgcheck' in data %}
    - gpgcheck: {{ data.gpgcheck }}
    {% endif %}
    {% if 'key_url' in data %}
    - key_url: {{ data.key_url }}
    {% endif %}
    {% if 'gpgautoimport' in data %}
    - gpgautoimport: {{ data.gpgautoimport }}
    {% endif %}
{% endfor %}
