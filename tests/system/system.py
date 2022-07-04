#!/usr/bin/env python3
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

"""System Test"""

import os
import sys
import re
import argparse

from hwcompatible.test import Test
from hwcompatible.command import Command
from hwcompatible.sysinfo import SysInfo
from hwcompatible.env import CertEnv
from hwcompatible.document import Document


class SystemTest(Test):
    """
    System Test
    """

    def __init__(self):
        Test.__init__(self)
        self.pri = 1
        self.sysinfo = SysInfo(CertEnv.releasefile)
        self.args = None
        self.logpath = ""

    def setup(self, args=None):
        """
        Initialization before test
        :param args:
        :return:
        """
        self.args = args or argparse.Namespace()
        self.logpath = getattr(args, "logdir", None) + "/system.log"

    def test(self):
        """
        test case
        :return:
        """
        os.system("uname -a &>> %s" % self.logpath)
        print("")
        os.system("lsmod &>> %s" % self.logpath)
        print("")
        os.system("dmidecode &>> %s" % self.logpath)
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
        """
        Check installed cert package
        :return:
        """
        print("\nChecking installed cert package...")
        return_code = True
        for cert_package in ["oec-hardware"]:
            rpm_verify = Command(
                "rpm -V --nomtime --nomode --nocontexts %s &>> %s" % (cert_package, self.logpath))
            try:
                rpm_verify.echo()
                sys.stdout.flush()
                if rpm_verify.output and len(rpm_verify.output) > 0:
                    return_code = False
            except Exception:
                print("Error: files in %s have been tampered." % cert_package)
                return_code = False
        return return_code

    def check_kernel(self):
        """
        Check kernel
        :return:
        """
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
                print("Error: kernel %s check GA status fail." %
                      self.sysinfo.kernel_version)
                return_code = False
        except Exception:
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

                if tainted & (1 << 12):
                    modules = self.get_modules("O")
                    print("Out-of-tree modules:")
                    for module in modules:
                        print(module)
                        # self.abi_check(module)
                        return_code = False
                    print("")

                if tainted & (1 << 13):
                    modules = self.get_modules("E")
                    print("Unsigned modules:")
                    for module in modules:
                        print(module)
                    print("")

            tainted_file.close()
        except Exception as concrete_error:
            print("Error: could not determine if kernel is tainted. \n",
                  concrete_error)
            return_code = False

        if os.system("rpm -V --nomtime --nomode --nocontexts %s" % kernel_rpm) != 0:
            print("Error: files from %s were modified.\n" % kernel_rpm)
            return_code = False

        try:
            params = Command("cat /proc/cmdline").get_str()
            print("Boot Parameters: %s" % params)
        except Exception as concrete_error:
            print("Error: could not determine boot parameters. \n", concrete_error)
            return_code = False

        return return_code

    def get_modules(self, sign):
        """
        Get the module with signs character
        :param sign:
        :return:
        """
        pattern = re.compile(r"^(?P<mod_name>\w+)[\s\S]+\((?P<signs>[A-Z]+)\)")
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
        """
        Check abi whitelist
        :param module:
        :return:
        """
        whitelist_path = [("/lib/modules/kabi-current/kabi_whitelist_" + self.sysinfo.arch),
                          ("/lib/modules/kabi/kabi_whitelist_" + self.sysinfo.arch),
                          ("/usr/src/kernels/%s/kabi_whitelist" %
                           self.sysinfo.kernel)
                          ]
        whitelist = ""
        for whitelist in whitelist_path:
            if os.path.exists(whitelist):
                break

        if not os.path.exists(whitelist):
            print(
                "Error: could not find whitelist file in any of the following locations:")
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
            print("Error: The following symbols are used by %s are not on the ABI \
            whitelist." % module)
            for symbol in black_symbols:
                print(symbol)
            return False

        print("")
        return True

    def read_abi_whitelist(self, whitelist):
        """
        Read abi whitelist
        :param whitelist:
        :return:
        """
        symbols = list()
        if not os.path.isfile(whitelist):
            print("Error: Cannot read whitelist file")
            return None

        whitelistfile = open(whitelist, "r")
        while True:
            line = whitelistfile.readline()
            if line == "":
                break
            if line == "\n":
                continue
            line.split()
            if line[0] == '[':
                # group = line[1:-2]
                continue
            symbol = line.strip()
            symbols.append(symbol)

        return symbols

    def read_module(self, module):
        """
        Read module
        :param module:
        :return:
        """
        symbols = list()
        module_file = self.get_modulefile(module)

        if not module_file:
            print("Error: Can not find module file for %s" % module)
            return None
        if not os.path.isfile(module_file):
            print("Error: Cannot read module file %s" % module_file)
            return None

        if module_file[-2:] == "ko":
            n_m = os.popen('modprobe --dump-modversions ' + module_file)
        else:
            n_m = open(module_file, "r")

        while True:
            line = n_m.readline()
            if line == "":
                break
            symbols.append(line)

        n_m.close()
        return self.readSymbols(symbols)

    def get_modulefile(self, module):
        """
        Get module file
        :param module:
        :return:
        """
        try:
            modulefile = Command("modinfo -F filename %s" % module).get_str()
            if os.path.islink(modulefile):
                modulefile = os.readlink(modulefile)
            return modulefile
        except Exception:
            print("Error: could no find module file for %s:" % module)
            return None

    def check_selinux(self):
        """
        check selinux
        :return:
        """
        print("\nChecking selinux...")
        status = os.system(
            "/usr/sbin/sestatus | grep 'SELinux status' | grep -qw 'enabled'")
        mode = os.system(
            "/usr/sbin/sestatus | grep 'Current mode' | grep -qw 'enforcing'")
        if mode == 0 and status == 0:
            print("SElinux is enforcing as expect.")
            return True
        else:
            print("SElinux is not enforcing, expect is enforcing.")
            os.system("/usr/sbin/sestatus")
            return False
