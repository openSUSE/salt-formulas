#
# spec file for package infrastructure-formulas
#
# Copyright (c) 2023 SUSE LLC
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
Version:        0.2
Release:        0
Summary:        Custom Salt states for the openSUSE/SUSE infrastructures
License:        GPL-3.0-or-later
Group:          System/Management
URL:            https://github.com/openSUSE/salt-formulas
Source:         _service
Requires:       infrastructure-formula
Requires:       libvirt-formula
Requires:       lunmap-formula
Requires:       orchestra-formula
Requires:       suse_ha-formula
BuildArch:      noarch

%description
Custom Salt states used in the openSUSE and SUSE infrastructures.

%package common
Summary:        Files and directories shared by formulas

%description common
Files and directories shared by openSUSE/SUSE infrastructure formuas.

%package -n infrastructure-formula
Summary:        Salt states specific to the openSUSE/SUSE infrastructures
Requires:       %{name}-common

%description -n infrastructure-formula
Custom Salt states specific to the openSUSE/SUSE infrastructures.

%package -n suse_ha-formula
Summary:        Salt states for managing SLE HA clusters
Requires:       %{name}-common

%description -n suse_ha-formula
Salt states for managing SUSE Linux Enterprise HA clusters.

%package -n libvirt-formula
Summary:        Salt states for managing libvirt
Requires:       %{name}-common

%description -n libvirt-formula
Salt states for managing libvirt servers.

%package -n lunmap-formula
Summary:        Salt states for managing lunmap
Requires:       %{name}-common

%description -n lunmap-formula
Salt states for managing LUN mappings.

%package -n orchestra-formula
Summary:        Salt orchestration helper states
Requires:       %{name}-common

%description -n orchestra-formula
Salt helper states for the openSUSE/SUSE infrastructure orchestration states.

%prep
mv %{_sourcedir}/salt-formulas-%{version}/* .

%build

%install
install -dm0755 %{buildroot}%{sdir} %{buildroot}%{mdir}

for formula in $(find -mindepth 1 -maxdepth 1 -type d -not -path './.git' -printf '%%P\n')
do
  echo "$formula"
  fname="${formula%%-*}"

  src_states="$formula/$fname"
  src_metadata="$formula/metadata"

  dst_states="%{sdir}/$fname"
  dst_metadata="%{mdir}/$fname"

  cp -rv "$src_states" "%{buildroot}$dst_states"
  echo "$dst_states" > "$fname.files"

  if [ -d "$src_metadata" ]
  then
    cp -rv "$src_metadata" "%{buildroot}$dst_metadata"
    echo "$dst_metadata" >> "$fname.files"
  fi
done

%files

%files common
%license COPYING
%doc README.md
%dir %{fdir}
%dir %{sdir}

%files -n infrastructure-formula -f infrastructure.files

%files -n suse_ha-formula -f suse_ha.files

%files -n libvirt-formula -f libvirt.files

%files -n lunmap-formula -f lunmap.files

%files -n orchestra-formula -f orchestra.files

%changelog
