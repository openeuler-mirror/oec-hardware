%define version    1.0.0
%define release    h1
%define debug_package %{nil}
%global _build_id_links none
%undefine __brp_mangle_shebangs

Name:           oec-hardware
Summary:        openEuler Hardware Certification Test Suite
Version:        %{version}
Release:        %{release}
Group:          Development/Tools
License:        Mulan PSL v2
URL:            https://gitee.com/openeuler/oec-hardware
Source0:        %{name}-%{version}-%{release}.tar.bz2

Buildroot:      %{_tmppath}/%{name}-%{version}-root
BuildRequires:  gcc
Requires:       kernel-devel, kernel-headers, dmidecode
Requires:       qperf, fio, memtester
Requires:       kernel >= 4
Requires:       python3

# server subpackage
%package server
Summary:        openEuler Hardware Certification Test Server
Group:          Development/Tools
Requires:       python3, python3-devel, nginx, qperf, psmisc

%description
openEuler Hardware Certification Test Suite

%description server
openEuler Hardware Certification Test Server

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
/usr/bin/eulercert
/usr/share/eulercert/kernelrelease.json
/usr/share/eulercert/lib/hwcert
/usr/share/eulercert/lib/tests
/usr/lib/systemd/system/eulercert.service
%dir /var/eulercert
%dir /usr/share/eulercert/lib
%dir /usr/share/eulercert

%files server
%defattr(-,root,root)
/usr/share/eulercert/lib/server
/usr/share/eulercert/lib/server/uwsgi.ini
/usr/share/eulercert/lib/server/uwsgi.conf
/usr/lib/systemd/system/eulercert-server.service

%postun
rm -rf /var/lock/eulercert.lock

%changelog
* Fri Jul 26 2019 Lu Tianxiong <lutianxiong@huawei.com> - 1.0.0-h1
- Initial spec

