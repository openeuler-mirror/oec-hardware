#!/usr/bin/env python3
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
# Desc: Public kabi test

import os
import argparse
from subprocess import getoutput
from hwcompatible.command import Command
from hwcompatible.test import Test
from hwcompatible.constants import TEST_KABI_ARCH
from hwcompatible.sysinfo import SysInfo
from hwcompatible.env import CertEnv
from hwcompatible.document import Document

kabi_dir = os.path.dirname(os.path.realpath(__file__))


class KabiTest(Test):
    def __init__(self):
        Test.__init__(self)
        self.kernel_version = getoutput("uname -r")
        self.requirements = ["gzip", "rpm-build"]
        self.symvers = None
        self.wl_logpath = ""
        self.miss_logpath = ""
        self.changed_logpath = ""
        self.sysinfo = SysInfo(CertEnv.releasefile)

    def setup(self, args=None):
        """
        Initialization before test
        """
        self.args = args or argparse.Namespace()
        self.logger = getattr(self.args, "test_logger", None)
        self.command = Command(self.logger)
        self.wl_logpath = os.path.join(
            self.logger.logdir, "kabi-whitelist.log")
        self.miss_logpath = os.path.join(
            self.logger.logdir, "kabi-missing.log")
        self.changed_logpath = os.path.join(
            self.logger.logdir, "kabi-changed.log")
        self.symvers = os.path.join(
            CertEnv.datadirectory, "symvers-" + self.kernel_version)

    def test(self):
        """
        Run kabi test case
        return: result
        """
        arch = self.command.run_cmd("uname -m")[0].strip()
        if arch not in TEST_KABI_ARCH:
            self.logger.info(" %s architecture does not support kabi testing." % arch)
            return True

        result = True
        self.logger.info("Start to test, please wait...")
        if not os.path.exists(self.symvers):
            symvers_gz = "symvers-" + self.kernel_version + ".gz"
            self.command.run_cmd("cp /boot/%s %s" %
                                 (symvers_gz, CertEnv.datadirectory))
            self.command.run_cmd("gzip -d %s/%s" %
                                 (CertEnv.datadirectory, symvers_gz))

        standard_symvers = self._get_kernel_source_rpm(arch)
        with open(standard_symvers, "r") as f:
            for line in f.readlines():
                line = line.strip().replace("\n", "")
                if line == "":
                    continue

                hsdp = line.split()
                if len(hsdp) < 4 :
                    continue

                result = self.command.run_cmd("grep %s %s" % (
                    hsdp[1], self.symvers), log_print=False)
                data = result[0]
                if data and hsdp[0] in data:
                    continue
                elif data and hsdp[0] not in data:
                    if not os.path.exists(self.changed_logpath):
                        self.command.run_cmd("echo 'standard_symvers     cur_symvers' | tee %s" % (
                            self.changed_logpath), log_print=False)

                    self.command.run_cmd("echo '{%s} {%s}' | tee %s" % (
                        line, data, self.changed_logpath), log_print=False)
                    result = False
                else:
                    self.command.run_cmd("echo '%s' | tee %s" % (
                        line, self.miss_logpath), log_print=False)
                    result = False

        if result:
            self.logger.info("Test kabi succeed.")
        else:
            self.logger.error("Test kabi failed.")

        return result

    def _get_kernel_source_rpm(self, arch):
        """
        get the path of kernel source rpm 
        """
        rpmpath = "/root/rpmbuild/SOURCES"
        standard_symvers = os.path.join(rpmpath, "Module.kabi_" + arch)
        if os.path.exists(standard_symvers):
            return standard_symvers

        product = self.sysinfo.product.split(" ")[0]
        if product == "openEuler":
            standard_kernel_version = getoutput(
                "dnf list --repo=source | grep '^kernel.src' | awk '{print $2}'")
            self.command.run_cmd("dnf download --source kernel-%s"
                                 % standard_kernel_version)
        elif product == "KylinSec":
            kylinsec_version = getoutput("cat /etc/dnf/vars/osversion | sed 's/[^0-9]//g'")
            kernel_dict = Document(CertEnv.kernelinfo, self.logger)
            if not kernel_dict.load():
                self.logger.error("Failed to get kernel info.")
                return False
            openeuler_version = kernel_dict.document[product][kylinsec_version].split('/')[0]
            standard_kernel_version = kernel_dict.document[product][kylinsec_version].split('/')[1]
            url = "https://repo.openeuler.org/%s/source/Packages/kernel-%s.src.rpm" \
                  % (openeuler_version, standard_kernel_version)
            self.command.run_cmd("wget %s -P %s" % (url, rpmpath))
        else:
            self.logger.info("Currently, this system is not supported to test kabi,"
                             " Please add the corresponding system in kernelrelease.json.")

        rpm = os.path.join("kernel-" + standard_kernel_version + ".src.rpm")
        getoutput("rpm -ivh %s" % rpm)
        os.remove(rpm)
        return standard_symvers
