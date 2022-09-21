%global _build_id_links none
%undefine __brp_mangle_shebangs

Name:           oec-hardware
Summary:        openEuler Hardware Compatibility Test Suite
Version:        1.1.2
Release:        4
Group:          Development/Tools
License:        Mulan PSL v2
URL:            https://gitee.com/openeuler/oec-hardware
Source0:        https://gitee.com/openeuler/oec-hardware/repository/archive/v%{version}.tar.gz

# patch fix issue
Patch0001:      oec-hardware-1.1.2-fix-oech.service_status_failed.patch
Patch0002:      oec-hardware-1.1.2-fix-system.patch
Patch0003:      oec-hardware-1.1.2-add-compatibility.patch
Patch0004:      oec-hardware-1.1.2-add-new-function-add-fixbug.patch

Buildroot:      %{_tmppath}/%{name}-%{version}-root
BuildRequires:  gcc
Requires:       kernel-devel, kernel-headers, dmidecode, tar
Requires:       kernel >= 4
Requires:       python3, python3-pyyaml, python3-concurrent-log-handler
Provides:       libswsds.so()(64bit)

# server subpackage
%package server
Summary:        openEuler Hardware Compatibility Test Server
Group:          Development/Tools
Requires:       python3, python3-devel, python3-flask, python3-uWSGI
Requires:       nginx, tar, qperf, psmisc

%description
openEuler Hardware Compatibility Test Suite

%description server
openEuler Hardware Compatibility Test Server

%prep
%setup -q -c
%patch1 -p1
%patch2 -p1
%patch3 -p1
%patch4 -p1

%build

sed -i '15i CFLAGS+=-g -fstack-protector-strong' tests/memory/Makefile

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
/usr/share/oech/lib/tests
/usr/share/oech/lib/config
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
* Wed Sep 21 2022 cuixucui <cuixucui1@h-partners.com> - 1.1.2-4
- Add requirements for system and bugfix
- Upgrade oec-hardware-server
- Update readme and design doc
- Fix nvme error
- Update network fibre check and log 
- Update description for perf test
- Add automatic configuration network card IP 


* Tue Sep 06 2022 meitingli <bubble_mt@outlook.com> - 1.1.2-3
- Add generate compatibility information
- Fix gpu and keycard issues

* Mon Sep 05 2022 cuixucui <cuixucui1@h-partners.com> - 1.1.2-2
- Fix Check whether the tool is modified failed

* Sat Sep 03 2022 ylzhangah <zhangyale3@h-partners.com> - 1.1.2-1
- Fix the status failed in checking oech.service status after stoped oech.service

* Tue Aug 30 2022 ylzhangah <zhangyale3@h-partners.com> - 1.1.2-0
- Upgrade command module
- Add VGPU testsuite
- Bugfix;

* Wed Aug 24 2022 wangkai <wangkai385@h-partners.com> - 1.1.1-6
- Enable debuginfo for fix strip

* Wed Aug 17 2022 zhangzikang <zhangzikang@kylinos.cn> - 1.1.1-5
- Fix server.py variable conflict issues in some system environment

* Wed Aug 10 2022 ylzhangah <1194926515@qq.com> - 1.1.1-4
- Fix rebootup issues
- Fix the issue that oech.service cannot be started

* Wed Aug 3 2022 cuixucui <cuixucui1@h-partners> - 1.1.1-3
- Fix the problem that the client fails to send messages after the server port is modified
- Fix the problem that the system test item failed to check the integrity of the software package

* Mon Aug 1 2022 cuixucui <cuixucui1@h-partners> - 1.1.1-2
- Fix the problem that FC and raid cannot get the new hard disk partition

* Sat Jul 30 2022 ylzhangah <1194926515@qq.com> - 1.1.1-1
- Change the version in version.config to 1.1.1

* Wed Jul 27 2022 cuixucui <cuixucui1@h-partners.com> - 1.1.1-0
-1. Reconstruct the log module and rectify the log printing
-2. Add kabi testcase
-3. Add driver, driver version, chip and module display to the console
-4. Add configuration file for testsuite to improve automation rate
-5. Add oech and oech-server version display
-6. Add driver information display in hardware test logs

* Fri Jul 08 2022 meitingli <bubble_mt@outlook.com> - 1.1.0-1
- Fix oech.server message display, change python version to python3

* Mon May 30 2022 meitingli <bubble_mt@outlook.com> - 1.1.0-0
- 1. Add support os version: openEuler 22.03LTS
- 2. Add FC/RAID/keycard/GPU/infiniband testcases
- 3. Bugfix

* Thu Sep 09 2021 Cui XuCui <cuixucui1@huawei.com> - 1.0.0-8
* Thu Jul 15 2021 zhangzikang <zhangzikang@kylinos.cn> - 1.0.0-7
- Fix cdrom and cpufreq test failed

* Fri Mar 19 2021 caodongxia <caodongxia@huawei.com> - 1.0.0-6
* Tue Sep 29 2020 Cui XuCui <cuixucui1@huawei.com> - 1.0.0-5
* Fri Jul 24 2020 Cui XuCui <cuixucui1@huawei.com> - 1.0.0-4
* Sun Jul 18 2020 Cui XuCui <cuixucui1@huawei.com> - 1.0.0-3
* Wed Jul 01 2020 Cui XuCui <cuixucui1@huawei.com> - 1.0.0-2
* Fri Jul 26 2019 Lu Tianxiong <lutianxiong@huawei.com> - 1.0.0-h1
- Initial spec

