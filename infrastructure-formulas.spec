#
# spec file for package infrastructure-formulas
#
# Copyright (c) 2025 SUSE LLC
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
%define pythons python3
Name:           infrastructure-formulas
Version:        3.1.0
Release:        0
Summary:        Salt states for openSUSE and SLE
License:        GPL-3.0-or-later
Group:          System/Management
URL:            https://github.com/openSUSE/salt-formulas
Source:         _service
Requires:       apache_httpd-formula
Requires:       backupscript-formula
Requires:       bootloader-formula
Requires:       doofetch-formula
Requires:       gitea-formula
Requires:       grains-formula
Requires:       hosts-formula
Requires:       infrastructure-formula
Requires:       jenkins-formula
Requires:       juniper_junos-formula
Requires:       kexec-formula
Requires:       libvirt-formula
Requires:       lldpd-formula
Requires:       lock-formula
Requires:       lunmap-formula
Requires:       mtail-formula
Requires:       multipath-formula
Requires:       network-formula
Requires:       orchestra-formula
Requires:       os_update-formula
Requires:       php_fpm-formula
Requires:       rebootmgr-formula
Requires:       redis-formula
Requires:       redmine-formula
Requires:       rsync-formula
Requires:       security-formula
Requires:       smartmontools-formula
Requires:       status_mail-formula
Requires:       suse_ha-formula
Requires:       sysconfig-formula
Requires:       tayga-formula
Requires:       zypper-formula
BuildArch:      noarch

%description
Salt states for managing applications running on openSUSE or SUSE Linux Enterprise based minions.

%package common
Summary:        Files and directories shared by formulas
License:        GPL-3.0-or-later

%description common
Files and directories shared by openSUSE/SUSE infrastructure formuas.

%package -n apache_httpd-formula
Summary:        Salt states for managing the Apache httpd
License:        GPL-3.0-or-later
Requires:       %{name}-common
Requires:       sysconfig-formula

%description -n apache_httpd-formula
Salt states for installing and configuring the Apache HTTP server on SUSE distributions.

%package -n backupscript-formula
Summary:        Salt states for managing SUSE backup scripts
License:        GPL-3.0-or-later
Requires:       %{name}-common
Requires:       sysconfig-formula

%description -n backupscript-formula
Salt states for installing and configuring the SUSE backup scripts for MySQL and PostgreSQL.

%package -n bootloader-formula
Summary:        Salt states for managing the bootloader
License:        GPL-3.0-or-later
Requires:       %{name}-common
Requires:       sysconfig-formula

%description -n bootloader-formula
Salt states for managing the bootloader setup and GRUB configuration.

%package -n doofetch-formula
Summary:        Salt states for managing doofetch
License:        GPL-3.0-or-later
Requires:       %{name}-common
Requires:       sysconfig-formula

%description -n doofetch-formula
Salt states for installing and configuring doofetch.

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

%package -n hosts-formula
Summary:        Salt states for managing %{_sysconfdir}/hosts
License:        GPL-3.0-or-later
Requires:       %{name}-common

%description -n hosts-formula
Salt states for managing the %{_sysconfdir}/hosts file.

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
Requires:       sysconfig-formula

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
Requires:       sysconfig-formula

%description -n libvirt-formula
Salt states for managing libvirt servers.

%package -n lldpd-formula
Summary:        Salt states for managing lldpd
License:        GPL-3.0-or-later
Requires:       %{name}-common
Requires:       sysconfig-formula

%description -n lldpd-formula
Salt states for installing and configuring lldpd.

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

%package -n mtail-formula
Summary:        Salt states for managing mtail
License:        GPL-3.0-or-later
Requires:       %{name}-common
Requires:       sysconfig-formula

%description -n mtail-formula
Salt states for managing mtail.

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
Requires:       sysconfig-formula

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

%package -n php_fpm-formula
Summary:        Salt states for managing PHP FPM
License:        GPL-3.0-or-later
Requires:       %{name}-common

%description -n php_fpm-formula
Salt states for managing PHP FPM.

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

%package -n security-formula
Summary:        Salt states for managing permissions
License:        GPL-3.0-or-later
Requires:       %{name}-common
Requires:       sysconfig-formula

%description -n security-formula
Salt states for configuring permissions and capabilities.

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
Requires:       sysconfig-formula

%description -n suse_ha-formula
Salt states for managing SUSE Linux Enterprise HA clusters.

%package -n sysconfig-formula
Summary:        Salt helpers for sysconfig
License:        GPL-3.0-or-later
Requires:       %{name}-common

%description -n sysconfig-formula
Library formula containing helper code for managing fillup/sysconfig files.

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

%package -n infrastructure-formula-python
Summary:        Infrastructure pillar helpers
License:        GPL-3.0-or-later
BuildRequires:  %{python_module pip}
BuildRequires:  %{python_module setuptools}
BuildRequires:  %{python_module wheel}
BuildRequires:  %{pythons}
BuildRequires:  python-rpm-macros
BuildArch:      noarch

%description -n infrastructure-formula-python
Python libraries to help with rendering Salt formula pillars using YAML datasets found in the openSUSE infrastructure.

%prep
mv %{_sourcedir}/salt-formulas-%{version}/* .

%build
pushd infrastructure-formula/python
%pyproject_wheel
popd

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
  dst_metadata="%{mdir}/$fname"

  src_states="$formula/$fname"
  dst_states="%{sdir}/$fname"
  if [ ! -d "$src_states" ]
  then
    fname_sub="${fname//_/-}"
    src_states="$formula/$fname_sub"
    dst_states="%{sdir}/$fname_sub"
  fi

  src_execumodules="$formula/_modules"
  src_statemodules="$formula/_states"
  src_bin="$formula/bin"

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

pushd infrastructure-formula/python
%pyproject_install
popd

%files

%files common
%license COPYING
%doc README.md
%dir %{fdir}
%dir %{mdir}
%dir %{sdir}
%dir %{sdir}/_{modules,states}

%files -n apache_httpd-formula -f apache_httpd.files

%files -n backupscript-formula -f backupscript.files

%files -n bootloader-formula -f bootloader.files

%files -n doofetch-formula -f doofetch.files

%files -n gitea-formula -f gitea.files

%files -n grains-formula -f grains.files

%files -n hosts-formula -f hosts.files

%files -n infrastructure-formula -f infrastructure.files

%files -n jenkins-formula -f jenkins.files

%files -n juniper_junos-formula -f juniper_junos.files

%files -n kexec-formula -f kexec.files

%files -n libvirt-formula -f libvirt.files

%files -n lldpd-formula -f lldpd.files

%files -n lock-formula -f lock.files

%files -n lunmap-formula -f lunmap.files

%files -n mtail-formula -f mtail.files

%files -n multipath-formula -f multipath.files

%files -n network-formula -f network.files

%files -n orchestra-formula -f orchestra.files

%files -n os_update-formula -f os_update.files

%files -n php_fpm-formula -f php_fpm.files

%files -n rebootmgr-formula -f rebootmgr.files

%files -n redis-formula -f redis.files

%files -n redmine-formula -f redmine.files

%files -n rsync-formula -f rsync.files

%files -n security-formula -f security.files

%files -n smartmontools-formula -f smartmontools.files

%files -n status_mail-formula -f status_mail.files

%files -n suse_ha-formula -f suse_ha.files

%files -n sysconfig-formula -f sysconfig.files

%files -n tayga-formula -f tayga.files

%files -n zypper-formula -f zypper.files

%files -n infrastructure-formula-python
%dir %{python_sitelib}/opensuse_infrastructure_formula
%pycache_only %{python_sitelib}/opensuse_infrastructure_formula/__pycache__
%{python_sitelib}/opensuse_infrastructure_formula/__{init,version}__.py
%dir %{python_sitelib}/opensuse_infrastructure_formula/pillar
%pycache_only %{python_sitelib}/opensuse_infrastructure_formula/pillar/__pycache__
%{python_sitelib}/opensuse_infrastructure_formula/pillar/*.py
%{python_sitelib}/opensuse_infrastructure_formula-*.dist-info

%changelog
