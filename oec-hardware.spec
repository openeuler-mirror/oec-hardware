%define version    1.1.0
%define release    0
%define debug_package %{nil}
%global _build_id_links none
%undefine __brp_mangle_shebangs

Name:           oec-hardware
Summary:        openEuler Hardware Compatibility Test Suite
Version:        %{version}
Release:        %{release}
Group:          Development/Tools
License:        Mulan PSL v2
URL:            https://gitee.com/openeuler/oec-hardware
Source0:        %{name}-%{version}.tar.bz2

Buildroot:      %{_tmppath}/%{name}-%{version}-root
BuildRequires:  gcc
Requires:       kernel-devel, kernel-headers, dmidecode, tar, python3-pyyaml
Requires:       qperf, fio, memtester
Requires:       kernel >= 4
Requires:       python3

# server subpackage
%package server
Summary:        openEuler Hardware Compatibility Test Server
Group:          Development/Tools
Requires:       python3, python3-devel, nginx, tar, qperf, psmisc

%description
openEuler Hardware Compatibility Test Suite

%description server
openEuler Hardware Compatibility Test Server

%prep
%setup -q -c

%build
[ "$RPM_BUILD_ROOT" != "/" ] && [ -d $RPM_BUILD_ROOT ] && rm -rf $RPM_BUILD_ROOT;
DESTDIR=$RPM_BUILD_ROOT VERSION_RELEASE=%{version} make

%install
DESTDIR=$RPM_BUILD_ROOT make install

%clean
[ "$RPM_BUILD_ROOT" != "/" ] && [ -d $RPM_BUILD_ROOT ] && rm -rf $RPM_BUILD_ROOT;

%pre

%post

%files
%defattr(-,root,root)
/usr/bin/oech
/usr/share/oech/kernelrelease.json
/usr/share/oech/lib/hwcompatible
/usr/share/oech/lib/config
/usr/share/oech/lib/tests
/usr/lib/systemd/system/oech.service
%dir /var/oech
%dir /usr/share/oech/lib
%dir /usr/share/oech

%files server
%defattr(-,root,root)
/usr/bin/oech-server
/usr/share/oech/lib/server
/usr/share/oech/lib/config
/usr/lib/systemd/system/oech-server.service

%postun
rm -rf /var/lock/oech.lock

%changelog
* Mon May 30 2022 meitingli <bubble_mt@outlook.com> - 1.1.0-0
- 1. Add support os version: openEuler 22.03LTS
- 2. Add FC/RAID/keycard/GPU/infiniband testcases
- 3. Bugfix

* Fri Jul 26 2019 Lu Tianxiong <lutianxiong@huawei.com> - 1.0.0-h1
- Initial spec

