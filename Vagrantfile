# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.provider "libvirt"
  config.vm.box = "tumbleweed-salt"
  config.vm.box_url = "https://download.opensuse.org/repositories/home:/crameleon:/appliances/openSUSE_Tumbleweed/Tumbleweed.x86_64-libvirt.box"
  config.vm.provision "shell", env: {"APPLY" => ENV['APPLY']}, inline: <<-SHELL
  if [ ! -d /srv/formulas ]
  then
    mkdir /srv/formulas
  fi
  if [ ! -d /srv/pillar/samples ]
  then
    mkdir /srv/pillar/samples
  fi
  for formula in $(find /vagrant -mindepth 1 -maxdepth 1 -type d -name '*-formula' -printf '%P\\n')
  do
    echo "$formula"
    fname="${formula%%-*}"
    src_states="$formula/$fname"
    src_formula="/vagrant/$src_states"
    src_pillar="/vagrant/$formula/pillar.example"
    if [ ! -d "$src_formula" ]
    then
      fname="${fname//_/-}"
      src_states="$formula/$fname"
      src_formula="/vagrant/$src_states"
    fi
    if [ ! -h "/srv/formulas/$fname" ]
    then
      ln -s "$src_formula" "/srv/formulas"
    fi
    if [ -f "$src_pillar" ]
    then
      cp "$src_pillar" "/srv/pillar/samples/$fname.sls"
    fi
  done
  printf 'file_roots:\n  base:\n    - /srv/salt\n    - /srv/formulas\n' > /etc/salt/minion.d/roots.conf
  tee /srv/pillar/top.sls >/dev/null <<EOF
{{ saltenv }}:
  '*':
    - full
EOF
  tee /srv/pillar/full.sls >/dev/null <<EOF
include:
  - samples.*
EOF
  echo "$APPLY"
  if [ -n "$APPLY" ]
  then
    salt-call --local state.apply "$APPLY"
  fi
  SHELL
  config.vm.define "masterless", primary: true do |vmconfig|
    vmconfig.vm.hostname = "saltomat"
    vmconfig.vm.provider :libvirt do |libvirt|
      libvirt.memory = 1024
    end
  end
end
