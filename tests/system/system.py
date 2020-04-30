#!/usr/bin/env python
# coding: utf-8

# Copyright (c) 2020 Huawei Technologies Co., Ltd.
# oec-hardware is licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Create: 2020-04-01

import os
import sys
import re
import shutil
import argparse

from hwcert.test import Test
from hwcert.command import Command, CertCommandError
from hwcert.sysinfo import SysInfo
from hwcert.env import CertEnv
from hwcert.document import Document


class SystemTest(Test):

    def __init__(self):
        Test.__init__(self)
        self.pri = 1
        self.sysinfo = SysInfo(CertEnv.releasefile)

    def setup(self, args=None):
        self.args = args or argparse.Namespace()
        self.logdir = getattr(args, "logdir", None)

    def test(self):
        os.system("uname -a")
        print("")
        os.system("lsmod")
        print("")
        os.system("dmidecode")
        sys.stdout.flush()

        return_code = True
        if not self.check_certrpm():
            return_code = False

        if not self.check_kernel():
            return_code = False

        if not self.check_selinux():
            return_code = False

        return return_code

    def check_certrpm(self):
        print("\nChecking installed cert package...")
        return_code = True
        for cert_package in ["oec-hardware"]:
            rpm_verify = Command("rpm -V --nomtime --nomode --nocontexts %s" % cert_package)
            try:
                rpm_verify.echo()
                sys.stdout.flush()
                if rpm_verify.output and len(rpm_verify.output) > 0:
                    return_code = False
            except:
                print("Error: files in %s have been tampered." % cert_package)
                return_code = False
        return return_code

    def check_kernel(self):
        print("\nChecking kernel...")
        kernel_rpm = self.sysinfo.kernel_rpm
        os_version = self.sysinfo.product + " " + self.sysinfo.get_version()
        print("Kernel RPM: %s" % kernel_rpm)
        print("OS Version: %s" % os_version)
        print("")
        return_code = True
        if self.sysinfo.debug_kernel:
            print("Error: debug kernel.")
            return_code = False

        kernel_dict = Document(CertEnv.kernelinfo)
        if not kernel_dict.load():
            print("Error: get kernel info fail.")
            return False

        try:
            if kernel_dict.document[os_version] != self.sysinfo.kernel_version:
                print("Error: kernel %s check GA status fail." % self.sysinfo.kernel_version)
                return_code = False
        except:
            print("Error: %s is not supported." % os_version)
            return_code = False

        try:
            tainted_file = open("/proc/sys/kernel/tainted", "r")
            tainted = int(tainted_file.readline())
            if tainted != 0:
                print("Warning: kernel is tainted (value = %u)." % tainted)
                if tainted & 1:
                    print("Error: module with a non-GPL license has been loaded.")
                    return_code = False
                    modules = self.get_modules("P")
                    print("Non-GPL modules:")
                    for module in modules:
                        print(module)
                    print("")

                if tainted & (1<<12):
                    modules = self.get_modules("O")
                    print("Out-of-tree modules:")
                    for module in modules:
                        print(module)
                        #self.abi_check(module)
                        return_code = False
                    print("")

                if tainted & (1<<13):
                    modules = self.get_modules("E")
                    print("Unsigned modules:")
                    for module in modules:
                        print(module)
                    print("")

            tainted_file.close()
        except Exception as e:
            print(e)
            print("Error: could not determine if kernel is tainted.")
            return_code = False

        if not os.system("rpm -V --nomtime --nomode --nocontexts %s" % kernel_rpm) is 0:
            print("Error: files from %s were modified." % kernel_rpm)
            print("")
            return_code = False

        try:
            params = Command("cat /proc/cmdline").get_str()
            print("Boot Parameters: %s" % params)
        except Exception as e:
            print(e)
            print("Error: could not determine boot parameters.")
            return_code = False

        return return_code

    def get_modules(self, sign):
        pattern = re.compile("^(?P<mod_name>\w+)[\s\S]+\((?P<signs>[A-Z]+)\)")
        proc_modules = open("/proc/modules")
        modules = list()
        for line in proc_modules.readlines():
            match = pattern.match(line)
            if match:
                if sign in match.group("signs"):
                    modules.append(match.group("mod_name"))
        proc_modules.close()
        return modules

    def abi_check(self, module):
        whitelist_path = [("/lib/modules/kabi-current/kabi_whitelist_" + self.sysinfo.arch),
                              ("/lib/modules/kabi/kabi_whitelist_" + self.sysinfo.arch),
                              ("/usr/src/kernels/%s/kabi_whitelist" % self.sysinfo.kernel)
                            ]

        for whitelist in whitelist_path:
            if os.path.exists(whitelist):
                break

        if not os.path.exists(whitelist):
            print("Error: could not find whitelist file in any of the following locations:")
            print("\n".join(whitelist_path))
            return False

        whitelist_symbols = self.read_abi_whitelist(whitelist)
        if not whitelist_symbols:
            return False
        module_symbols = self.read_module(module)
        if not module_symbols:
            return False
        extra_symbols = list()
        for symbol in module_symbols:
            if symbol not in whitelist_symbols:
                extra_symbols.append(symbol)

        black_symbols = list()
        if extra_symbols:
            greylist = "/usr/share/doc/kmod-%s/greylist.txt" % module
            if os.path.exists(greylist):
                print("checking greylist for %s" % module)
                greylist_symbols = self.read_abi_whitelist(greylist)
                for symbol in extra_symbols:
                    if symbol not in greylist_symbols:
                        black_symbols.append(symbol)
            else:
                black_symbols = extra_symbols

        if black_symbols:
            print("Error: The following symbols are used by %s are not on the ABI whitelist." % module)
            for symbol in black_symbols:
                print(symbol)
            return False

        print("")
        return True

    def read_abi_whitelist(self, whitelist):
        symbols = list()
        if not os.path.isfile(whitelist):
            print("Error: Cannot read whitelist file")
            return None

        whitelistFile = open(whitelist,"r")
        while True:
            line = whitelistFile.readline()
            if line == "":
                break
            if line == "\n":
                continue
            line.split()
            if line[0] == '[':
                group=line[1:-2]
                continue
            symbol=line.strip()
            symbols.append(symbol)

        return symbols

    def read_module(self, module):
        symbols = list()
        modulefile = self.get_modulefile(module)

        if not modulefile:
            print("Error: Can not find module file for %s" % module)
            return None
        if not os.path.isfile(modulefile):
            print("Error: Cannot read module file %s" % modulefile)
            return None

        if modulefile[-2:] == "ko":
            nm = os.popen('modprobe --dump-modversions ' + modulefile)
        else:
            nm = open(modulefile,"r")

        while True:
            line = nm.readline()
            if line == "":
                break
            symbols.append(line)

        nm.close()
        return self.readSymbols(symbols)

    def get_modulefile(self, module):
        try:
            modulefile = Command("modinfo -F filename %s" % module).get_str()
            if os.path.islink(modulefile):
                modulefile = os.readlink(modulefile)
            return modulefile
        except:
            print("Error: could no find module file for %s:" % module)
            return None

    def check_selinux(self):
        print("\nChecking selinux...")
        status = os.system("/usr/sbin/sestatus | grep 'SELinux status' | grep -qw 'enabled'")
        mode = os.system("/usr/sbin/sestatus | grep 'Current mode' | grep -qw 'enforcing'")
        if mode == 0 and status == 0:
            print("SElinux is enforcing.")
            return True
        else:
            print("SElinux is not enforcing.")
            os.system("/usr/sbin/sestatus")
            return False
