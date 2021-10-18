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
    {% if 'gpgkey' in data or 'key_url' in data %}
    - gpgkey: {{ data.gpgkey | default(data.key_url) }}
    {% endif %}
    {% if 'gpgautoimport' in data %}
    - gpgautoimport: {{ data.gpgautoimport }}
    {% endif %}
{% endfor %}
