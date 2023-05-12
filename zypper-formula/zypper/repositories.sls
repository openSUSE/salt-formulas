{% set repositories = salt['pillar.get']('zypper:repositories', {}) %}

{% for repo, data in repositories.items() %}
{{ repo }}:
  pkgrepo.managed:
    - baseurl: {{ data.baseurl }}
    - enabled: {{ data.enabled | default(True) }}
    - priority: {{ data.priority | default(99) }}
    - gpgcheck: {{ data.gpgcheck | default(True) }}
    - refresh: {{ data.refresh | default(False) }}
    {% if 'gpgkey' in data or 'key_url' in data %}
    - gpgautoimport: {{ data.gpgautoimport | default(True) }}
    - gpgkey: {{ data.gpgkey | default(data.key_url) }}
    {% endif %}
{% endfor %}
