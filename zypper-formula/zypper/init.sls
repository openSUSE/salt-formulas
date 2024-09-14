include:
  - zypper.config
  - zypper.repositories
  {%- if grains['osmajorrelease'] < 15 %}
  - zypper.packages_legacy
  {%- else %}
  - zypper.packages
  {%- endif %}
  - zypper.variables
