#!/usr/bin/env python3
# coding: utf-8

# Copyright (c) 2020-2022 Huawei Technologies Co., Ltd.
# oec-hardware is licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Create: 2020-04-01
# Desc: System Test

import re
from subprocess import getoutput
from hwcompatible.test import Test
from hwcompatible.sysinfo import SysInfo
from hwcompatible.env import CertEnv
from hwcompatible.document import Document


class SystemTest(Test):
    def __init__(self):
        Test.__init__(self)
        self.pri = 1
        self.requirements = ["policycoreutils"]
        self.sysinfo = SysInfo(CertEnv.releasefile)

    def test(self):
        """
        test case
        :return:
        """
        self.command.run_cmd("uname -a", ignore_errors=True)
        self.command.run_cmd("lsmod",  ignore_errors=True)
        self.command.run_cmd("dmidecode", ignore_errors=True)

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
        self.logger.info("Checking installed cert package...")
        flag = True
        for cert_package in ["oec-hardware"]:
            rpm_verify = self.command.run_cmd(
                "rpm -V --nomtime --nomode --nocontexts %s" % cert_package, ignore_errors=True)
            if rpm_verify[2] == 0:
                continue

            output = rpm_verify[0].split('\n')
            for file in output:
                if not file or "test_config.yaml" in file or "pci.ids" in file:
                    continue
                flag = False
                self.logger.error(
                    "Files in %s have been tampered." % cert_package)
                self.logger.error(
                    "The tampered files are as follows:\n%s" % rpm_verify[0], terminal_print=False)
                break

        return flag

    def check_kernel(self):
        """
        Check kernel
        :return:
        """
        kernel_release = ""
        os_version = ""
        self.logger.info("Checking kernel...")
        product = self.sysinfo.product.split(" ")[0]
        kernel_rpm = self.sysinfo.kernel_rpm
        self.logger.info("Kernel RPM: %s" % kernel_rpm, terminal_print=False)
        if product == "openEuler":
            os_version = self.sysinfo.product + " " + self.sysinfo.get_version()
        elif product == "KylinSec":
            os_version = getoutput("cat /etc/dnf/vars/osversion | sed 's/[^0-9]//g'")
        else:
            self.logger.error("Failed to get os version info.")
        self.logger.info("OS Version: %s" % os_version, terminal_print=False)
        self.command.run_cmd("cat /proc/cmdline")
        return_code = True
        if self.sysinfo.debug_kernel:
            self.logger.error("This is debug kernel.")
            return_code = False

        kernel_dict = Document(CertEnv.kernelinfo, self.logger)
        if not kernel_dict.load():
            self.logger.error("Failed to get kernel info.")
            return False
        if product == "openEuler":
            kernel_release = kernel_dict.document[product][os_version]
        elif product == "KylinSec":
            kernel_release = kernel_dict.document[product][os_version].split('/')[1].split('-')[0]
        try:
            if kernel_release != self.sysinfo.kernel_version:
                self.logger.error("Failed to check kernel %s GA status." %
                                  self.sysinfo.kernel_version)
                return_code = False
        except Exception:
            self.logger.error("%s is not supported." % os_version)
            return_code = False

        try:
            with open("/proc/sys/kernel/tainted", "r") as tainted_file:
                tainted = int(tainted_file.readline())
                if tainted != 0:
                    self.logger.warning(
                        "kernel is tainted (value = %u)." % tainted)
                    if tainted & 1:
                        self.logger.warning(
                            "Module with a non-GPL license has been loaded.")
                        return_code = False
                        modules = self.get_modules("P")
                        self.logger.warning(
                            "Non-GPL modules:\n%s" % "\n".join(modules))

                    if tainted & (1 << 12):
                        modules = self.get_modules("O")
                        self.logger.error(
                            "Out-of-tree modules:\n%s" % "\n".join(modules))
                        return_code = False

                    if tainted & (1 << 13):
                        modules = self.get_modules("E")
                        self.logger.warning(
                            "Unsigned modules:\n%s" % "\n".join(modules))

        except Exception as concrete_error:
            self.logger.error("Unable to determine whether kernel has been tainted. \n",
                              concrete_error)
            return_code = False

        kernel_verfiy = self.command.run_cmd(
            "rpm -V --nomtime --nomode --nocontexts %s" % kernel_rpm)
        if kernel_verfiy[2] == 0:
            return return_code

        except_list = ["modules.dep", "modules.symbols", "modules.dep.bin", "modules.symbols.bin"]
        for line in kernel_verfiy[0].strip().split("\n"):
            if line.split("/")[-1] in except_list:
                continue
            else:
                self.logger.info("Files in %s were modified.\n" % kernel_rpm)
                self.logger.error("The tampered files are as follows:\n%s" % line, terminal_print=False)
                return_code = False
                break

        return return_code

    def get_modules(self, sign):
        """
        Get the module with signs character
        :param sign:
        :return:
        """
        pattern = re.compile(r"^(?P<mod_name>\w+)[\s\S]+\((?P<signs>[A-Z]+)\)")

        modules = list()
        with open("/proc/modules") as proc_modules:
            for line in proc_modules.readlines():
                match = pattern.match(line)
                if match and sign in match.group("signs"):
                    modules.append(match.group("mod_name"))

        return modules

    def check_selinux(self):
        """
        check selinux
        :return:
        """
        self.logger.info("Checking selinux...")
        status = self.command.run_cmd(
            "/usr/sbin/sestatus | grep 'SELinux status' | grep -qw 'enabled'")
        mode = self.command.run_cmd(
            "/usr/sbin/sestatus | grep 'Current mode' | grep -qw 'enforcing'")
        if status[2] == 0 and mode[2] == 0:
            self.logger.info("SElinux is enforcing as expect.")
            return True

        self.logger.error("SElinux is not enforcing, expect is enforcing.")
        self.command.run_cmd("/usr/sbin/sestatus")
        return False
