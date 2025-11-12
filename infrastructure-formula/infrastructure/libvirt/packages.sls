infrastructure_libvirt_packages:
  pkg.installed:
    - pkgs:
        - python3-libvirt-python
    - reload_modules: true
    - resolve_capabilities: true
