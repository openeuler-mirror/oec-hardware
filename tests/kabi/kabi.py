#!/usr/bin/env python
# coding: utf-8
# Copyright (c) 2022 Huawei Technologies Co., Ltd.
# oec-hardware is licensed under the Mulan PSL v2.gica's
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Author: @meitingli
# Create: 2022-05-30

"""public kabi test"""

import os
from hwcompatible.env import CertEnv
from hwcompatible.command import Command
from hwcompatible.test import Test

kabi_dir = os.path.dirname(os.path.realpath(__file__))


class KabiTest(Test):
    """
    kabi Test
    """

    def __init__(self):
        Test.__init__(self)
        self.logpath = None
        self.driver = None
        self.kernel_version = Command("uname -r").read()
        self.requirements = ["gzip", "rpm-build"]
        self.symvers = None
        self.white_list = None
        self.args = None
        self.wl_logpath = ""
        self.miss_logpath = ""
        self.changed_logpath = ""

    def setup(self, args=None):
        """
        Initialization before test
        """
        self.args = args or argparse.Namespace()
        self.wl_logpath = os.path.join(
            getattr(args, "logdir", None), "kabi-whitelist.log")
        self.miss_logpath = os.path.join(
            getattr(args, "logdir", None), "kabi-missing.log")
        self.changed_logpath = os.path.join(
            getattr(args, "logdir", None), "kabi-changed.log")
        self.symvers = os.path.join(
            CertEnv.datadirectory, "symvers-" + self.kernel_version)

    def test(self):
        """
        Run kabi test case
        return: result
        """
        result = True
        os_version = Command(
            "grep openeulerversion /etc/openEuler-latest | awk -F = '{print $2}'").read()
        print("Start to test, please wait...")
        if not os.path.exists(self.symvers):
            symvers_gz = "symvers-" + self.kernel_version + ".gz"
            Command("cp /boot/%s %s" %
                    (symvers_gz, CertEnv.datadirectory)).run()
            Command("gzip -d %s/%s" %
                    (CertEnv.datadirectory, symvers_gz)).run()

        arch = Command("uname -m").read()
        self.white_list = self._get_white_list(os_version, arch)
        if not self.white_list:
            print("Get kernel white list failed.")

        standard_symvers = self._get_kernel_source_rpm(os_version, arch)

        with open(standard_symvers, "r") as f:
            for line in f.readlines():
                line = line.strip().replace("\n", "")
                if line == "":
                    continue

                hsdp = line.split()
                if len(hsdp) < 4 or hsdp[1] in self.white_list:
                    continue

                data = Command("grep %s %s" % (hsdp[1], self.symvers)).read()
                if data and hsdp[0] in data:
                    continue
                elif data and hsdp[0] not in data:
                    if not self.changed_logpath.exists():
                        Command("echo 'standard_symvers     cur_symvers' >> %s" % (
                            self.changed_logpath)).run()

                    Command("echo '{%s} {%s}' >> %s" %
                            (line, data, self.changed_logpath)).run()
                    result = False
                else:
                    Command("echo '%s' >> %s" %
                            (line, self.miss_logpath)).run()
                    result = False

        if result:
            print("Test kabi succeed.")
        else:
            print("Test kabi failed.")

        return result

    def _get_white_list(self, os_version, arch):
        url = "https://gitee.com/src-openeuler/kernel/raw/%s/kabi_whitelist_%s" % (
            os_version, arch)
        white_list = os.path.join(
            CertEnv.datadirectory, "kabi_whitelist_" + arch)
        if not os.path.exists(white_list):
            Command("wget %s -P %s" % (url, CertEnv.datadirectory)).run_quiet()
        
        # Check download file
        if not os.path.exists(white_list):
            return False

        return white_list

    def _get_kernel_source_rpm(self, os_version, arch):
        standard_kernel_version = Command(
            "dnf list --repo=source | grep kernel.src | head -n 1 | awk '{print $2}'").read()
        rpmpath = "/root/rpmbuild/SOURCES"
        standard_symvers = os.path.join(rpmpath, "Module.kabi_" + arch)
        if os.path.exists(standard_symvers):
            return standard_symvers

        Command("dnf download --source kernel-%s" %
                standard_kernel_version).run()
        rpm = "kernel-" + standard_kernel_version + ".src.rpm"
        Command("rpm -ivh %s" % rpm).run_quiet()
        os.remove(rpm)
        return standard_symvers
