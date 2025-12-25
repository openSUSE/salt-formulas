hypervisor_directories:
  file.directory:
    - names:
      {%- for subdir in ['', 'agents', 'disks', 'disks/old', 'domains', 'networks', 'os-images', 'nvram'] %}
      - {{ salt['pillar.get']('infrastructure:kvm_topdir') }}/{{ subdir }}
      {%- endfor %}
