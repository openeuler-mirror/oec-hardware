%define version    1.1.5
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
Requires:       kernel-devel, kernel-headers, dmidecode, tar
Requires:       kernel >= 4
Requires:       python3, python3-pyyaml, python3-concurrent-log-handler, net-tools
Provides:       libswsds.so()(64bit)

# server subpackage
%package server
Summary:        openEuler Hardware Compatibility Test Server
Group:          Development/Tools
Requires:       python3, python3-devel, python3-flask, python3-uWSGI, python3-werkzeug, paramiko
Requires:       nginx, tar, qperf, psmisc, dpdk, dpdk-tools, dpdk-devel, net-tools, perftest

%description
openEuler Hardware Compatibility Test Suite

%description server
openEuler Hardware Compatibility Test Server

%prep
%setup -q -c

%build
%ifarch x86_64 aarch64
strip tests/compatible/keycard/libswsds_%{_arch}.so
%endif
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
/usr/share/oech/lib/oech_logrotate.sh
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
* Mon Oct 23 2023 liuyanze <liuyanze1@huawei.com> - 1.1.5-0
1. Add support for openEuler 20.03 LTS SP4, openEuler 22.03 LTS SP2, openEuler 22.03 LTS SP3
2. Add modifications to Kylinsec with oec-hardware
3. Add support for Loongson and SW architectures
4. Bugfix

* Tue Feb 28 2023 cuixucui <cuixucui1@h-partner.com> - 1.1.4-0
1. Add board information in the test report
2. Add spdk test case
3. Add dpdk test case
4. Bugfix

* Mon Oct 24 2022 meitingli <bubble_mt@outlook.com> - 1.1.3-0
1. Add support for openEuler 22.03LTS SP1
2. Add AMD GPU testcase
3. Add automatic configuration network card IP
4. Add generate compatibility information

* Mon Aug 29 2022 meitingli <bubble_mt@outlook.com> - 1.1.2-0
1. Upgrade command module
2. Add VGPU testsuite
3. Bugfix

* Wed Jul 27 2022 cuixucui <cuixucui1@h-partners.com> - 1.1.1-0
-1. Reconstruct the log module and rectify the log printing
-2. Add kabi testcase
-3. Add driver, driver version, chip and module display to the console
-4. Add configuration file for testsuite to improve automation rate
-5. Add oech and oech-server version display
-6. Add driver information display in hardware test logs

* Mon May 30 2022 meitingli <bubble_mt@outlook.com> - 1.1.0-0
- 1. Add support os version: openEuler 22.03LTS
- 2. Add FC/RAID/keycard/GPU/infiniband testcases
- 3. Bugfix

* Fri Jul 26 2019 Lu Tianxiong <lutianxiong@huawei.com> - 1.0.0-h1
- Initial spec

