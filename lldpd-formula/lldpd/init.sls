lldpd_package:
  pkg.installed:
    - name: lldpd

{%- if 'lldpd' in pillar and 'sysconfig' in pillar['lldpd'] %}
lldpd_sysconfig:
  suse_sysconfig.sysconfig:
    - name: lldpd
    - key_values: {{ pillar['lldpd']['sysconfig'] }}
    - require:
        - pkg: lldpd_package
{%- endif %}

lldpd_service:
  service.running:
    - name: lldpd
    - reload: false
    - require:
        - pkg: lldpd_package
    {%- if 'lldpd' in pillar and 'sysconfig' in pillar['lldpd'] %}
    - watch:
        - suse_sysconfig: lldpd_sysconfig
    {%- endif %}
