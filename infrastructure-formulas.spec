#
# spec file for package infrastructure-formulas
#
# Copyright (c) 2024 SUSE LLC
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.

# Please submit bugfixes or comments via https://bugs.opensuse.org/
#


%define fdir %{_datadir}/salt-formulas
%define sdir %{fdir}/states
%define mdir %{fdir}/metadata
Name:           infrastructure-formulas
Version:        1.5
Release:        0
Summary:        Custom Salt states for the openSUSE/SUSE infrastructures
License:        GPL-3.0-or-later
Group:          System/Management
URL:            https://github.com/openSUSE/salt-formulas
Source:         _service
Requires:       bootloader-formula
Requires:       gitea-formula
Requires:       grains-formula
Requires:       infrastructure-formula
Requires:       jenkins-formula
Requires:       juniper_junos-formula
Requires:       kexec-formula
Requires:       libvirt-formula
Requires:       lock-formula
Requires:       lunmap-formula
Requires:       multipath-formula
Requires:       network-formula
Requires:       orchestra-formula
Requires:       os_update-formula
Requires:       rebootmgr-formula
Requires:       redis-formula
Requires:       redmine-formula
Requires:       rsync-formula
Requires:       smartmontools-formula
Requires:       status_mail-formula
Requires:       suse_ha-formula
Requires:       tayga-formula
Requires:       zypper-formula
BuildArch:      noarch

%description
Custom Salt states used in the openSUSE and SUSE infrastructures.

%package common
Summary:        Files and directories shared by formulas
License:        GPL-3.0-or-later

%description common
Files and directories shared by openSUSE/SUSE infrastructure formuas.

%package -n bootloader-formula
Summary:        Salt states for managing the bootloader
License:        GPL-3.0-or-later
Requires:       %{name}-common

%description -n bootloader-formula
Salt states for managing the bootloader setup and GRUB configuration.

%package -n gitea-formula
Summary:        Salt states for managing Gitea
License:        GPL-3.0-or-later
Requires:       %{name}-common

%description -n gitea-formula
Salt states for managing Gitea.

%package -n grains-formula
Summary:        Salt state for managing grains
License:        Apache-2.0
Requires:       %{name}-common

%description -n grains-formula
Salt state for managing grains.

%package -n infrastructure-formula
Summary:        Salt states specific to the openSUSE/SUSE infrastructures
License:        GPL-3.0-or-later
Requires:       %{name}-common

%description -n infrastructure-formula
Custom Salt states specific to the openSUSE/SUSE infrastructures.

%package -n jenkins-formula
Summary:        Salt states for managing Jenkins
License:        GPL-3.0-or-later
Requires:       %{name}-common

%description -n jenkins-formula
Salt states for managing Jenkins Controller and Agent servers

%package -n juniper_junos-formula
Summary:        Salt states for managing Junos
License:        GPL-3.0-or-later
Requires:       %{name}-common

%description -n juniper_junos-formula
Salt states for managing Juniper Junos based network devices using pillars.

%package -n kexec-formula
Summary:        Salt states for managing Kexec
License:        GPL-3.0-or-later
Requires:       %{name}-common

%description -n kexec-formula
Salt states for managing Kexec using the kexec-load service

%package -n libvirt-formula
Summary:        Salt states for managing libvirt
License:        GPL-3.0-or-later
Requires:       %{name}-common

%description -n libvirt-formula
Salt states for managing libvirt servers.

%package -n lock-formula
Summary:        Salt state module for managing lockfiles
License:        GPL-3.0-or-later
Requires:       %{name}-common

%description -n lock-formula
Salt state module allowing you to place a lock file prior to other states in order to prevent simultaneous executions.

%package -n lunmap-formula
Summary:        Salt states for managing lunmap
License:        GPL-3.0-or-later
Requires:       %{name}-common

%description -n lunmap-formula
Salt states for managing LUN mappings.

%package -n multipath-formula
Summary:        Salt states for managing multipath
License:        GPL-3.0-or-later
Requires:       %{name}-common

%description -n multipath-formula
Salt states for installing multipath-tools and managing multipath/multipathd

%package -n network-formula
Summary:        Salt states for managing the network
License:        GPL-3.0-or-later
Requires:       %{name}-common

%description -n network-formula
Salt states for managing the network configuration using backends like Wicked.

%package -n orchestra-formula
Summary:        Salt orchestration helper states
License:        GPL-3.0-or-later
Requires:       %{name}-common

%description -n orchestra-formula
Salt helper states for the openSUSE/SUSE infrastructure orchestration states.

%package -n os_update-formula
Summary:        Salt states for managing os-update
License:        GPL-3.0-or-later
Requires:       %{name}-common

%description -n os_update-formula
Salt states for managing os-update.

%package -n rebootmgr-formula
Summary:        Salt states for managing rebootmgr
License:        GPL-3.0-or-later
Requires:       %{name}-common

%description -n rebootmgr-formula
Salt states for managing rebootmgr.

%package -n redis-formula
Summary:        Salt states for managing Redis
License:        GPL-3.0-or-later
Requires:       %{name}-common

%description -n redis-formula
Salt states for managing Redis.

%package -n redmine-formula
Summary:        Salt states for managing Redmine
License:        GPL-3.0-or-later
Requires:       %{name}-common

%description -n redmine-formula
Salt states for managing Redmine.

%package -n rsync-formula
Summary:        Salt states for managing rsyncd
License:        GPL-3.0-or-later
Requires:       %{name}-common

%description -n rsync-formula
Salt states for managing rsyncd.

%package -n smartmontools-formula
Summary:        Salt states for managing smartmontools
License:        GPL-3.0-or-later
Requires:       %{name}-common

%description -n smartmontools-formula
Salt states for installing smartmontools and configuring smartd

%package -n status_mail-formula
Summary:        Salt states for managing systemd-status-mail
License:        GPL-3.0-or-later
Requires:       %{name}-common

%description -n status_mail-formula
Salt states for managing systemd-status-mail.

%package -n suse_ha-formula
Summary:        Salt states for managing SLE HA clusters
License:        GPL-3.0-or-later
Requires:       %{name}-common

%description -n suse_ha-formula
Salt states for managing SUSE Linux Enterprise HA clusters.

%package -n tayga-formula
Summary:        Salt states for managing TAYGA
License:        GPL-3.0-or-later
Requires:       %{name}-common

%description -n tayga-formula
Salt states for managing the TAYGA NAT64 daemon

%package -n zypper-formula
Summary:        Salt states for managing zypper
License:        Apache-2.0
Requires:       %{name}-common

%description -n zypper-formula
Salt states for configuring packages, repositories, and zypper itself.

%prep
mv %{_sourcedir}/salt-formulas-%{version}/* .

%build

%install
install -dm0755 %{buildroot}%{mdir} %{buildroot}%{sdir} %{buildroot}%{sdir}/_modules %{buildroot}%{sdir}/_states %{buildroot}%{_bindir}

dst_execumodules="%{sdir}/_modules"
dst_statemodules="%{sdir}/_states"
dst_bin='%{_bindir}'

for formula in $(find -mindepth 1 -maxdepth 1 -type d -name '*-formula' -printf '%%P\n')
do
  echo "$formula"
  fname="${formula%%-*}"

  src_metadata="$formula/metadata"
  src_states="$formula/$fname"
  if [ ! -d "$src_states" ]
  then
    src_states="$formula/${fname//_/-}"
  fi
  src_execumodules="$formula/_modules"
  src_statemodules="$formula/_states"
  src_bin="$formula/bin"

  dst_metadata="%{mdir}/$fname"
  dst_states="%{sdir}/$fname"

  if [ -d "$src_metadata" ]
  then
    cp -rv "$src_metadata" "%{buildroot}$dst_metadata"
    echo "$dst_metadata" > "$fname.files"
  fi

  if [ -d "$src_states" ]
  then
    cp -rv "$src_states" "%{buildroot}$dst_states"
    echo "$dst_states" >> "$fname.files"
  else
    echo "Warning: $formula does not ship with any states"
  fi

  for mod in execu state bin
  do
    mode=0644
    case "$mod" in
      'execu' ) src="$src_execumodules"
                dst="$dst_execumodules"
      ;;
      'state' ) src="$src_statemodules"
                dst="$dst_statemodules"
      ;;
      'bin' )
                src="$src_bin"
                dst="$dst_bin"
                mode=0755
      ;;
    esac

    if [ -d "$src" ]
    then
      find "$src" -type f \
        -execdir install -vm "$mode" {} "%{buildroot}$dst" \; \
        -execdir sh -cx 'echo "$1/$(basename $2)" >> "$3"' prog "$dst" {} "../../$fname.files" \;
    fi
  done

  for license in 'COPYING' 'LICENCE' 'LICENSE'
  do
    if [ -f "$formula/$license" ]
    then
      echo "%%license $formula/$license" >> "$fname.files"
      break
    fi
  done

done

%files

%files common
%license COPYING
%doc README.md
%dir %{fdir}
%dir %{mdir}
%dir %{sdir}
%dir %{sdir}/_{modules,states}

%files -n bootloader-formula -f bootloader.files

%files -n gitea-formula -f gitea.files

%files -n grains-formula -f grains.files

%files -n infrastructure-formula -f infrastructure.files

%files -n jenkins-formula -f jenkins.files

%files -n juniper_junos-formula -f juniper_junos.files

%files -n kexec-formula -f kexec.files

%files -n libvirt-formula -f libvirt.files

%files -n lock-formula -f lock.files

%files -n lunmap-formula -f lunmap.files

%files -n multipath-formula -f multipath.files

%files -n network-formula -f network.files

%files -n orchestra-formula -f orchestra.files

%files -n os_update-formula -f os_update.files

%files -n rebootmgr-formula -f rebootmgr.files

%files -n redis-formula -f redis.files

%files -n redmine-formula -f redmine.files

%files -n rsync-formula -f rsync.files

%files -n smartmontools-formula -f smartmontools.files

%files -n status_mail-formula -f status_mail.files

%files -n suse_ha-formula -f suse_ha.files

%files -n tayga-formula -f tayga.files

%files -n zypper-formula -f zypper.files

%changelog
