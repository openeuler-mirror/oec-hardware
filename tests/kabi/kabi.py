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
from hwcompatible.env import CertEnv
from hwcompatible.command import Command
from hwcompatible.test import Test

kabi_dir = os.path.dirname(os.path.realpath(__file__))


class KabiTest(Test):
    def __init__(self):
        Test.__init__(self)
        self.kernel_version = getoutput("uname -r")
        self.requirements = ["gzip", "rpm-build"]
        self.symvers = None
        self.white_list = None
        self.wl_logpath = ""
        self.miss_logpath = ""
        self.changed_logpath = ""

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
        result = True
        os_version = getoutput(
            "grep openeulerversion /etc/openEuler-latest | awk -F = '{print $2}'")
        self.logger.info("Start to test, please wait...")
        if not os.path.exists(self.symvers):
            symvers_gz = "symvers-" + self.kernel_version + ".gz"
            self.command.run_cmd("cp /boot/%s %s" %
                                 (symvers_gz, CertEnv.datadirectory))
            self.command.run_cmd("gzip -d %s/%s" %
                                 (CertEnv.datadirectory, symvers_gz))

        arch = getoutput("uname -m")
        self.white_list = self._get_white_list(os_version, arch)
        if not self.white_list:
            self.logger.error("Get kernel white list failed.")

        standard_symvers = self._get_kernel_source_rpm(arch)

        with open(standard_symvers, "r") as f:
            for line in f.readlines():
                line = line.strip().replace("\n", "")
                if line == "":
                    continue

                hsdp = line.split()
                if len(hsdp) < 4 or hsdp[1] in self.white_list:
                    continue

                result = self.command.run_cmd("grep %s %s" % (
                    hsdp[1], self.symvers), log_print=False)
                data = result[0]
                if data and hsdp[0] in data:
                    continue
                elif data and hsdp[0] not in data:
                    if not self.changed_logpath.exists():
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

    def _get_white_list(self, os_version, arch):
        url = "https://gitee.com/src-openeuler/kernel/raw/%s/kabi_whitelist_%s" % (
            os_version, arch)
        white_list = os.path.join(
            CertEnv.datadirectory, "kabi_whitelist_" + arch)
        if not os.path.exists(white_list):
            self.command.run_cmd("wget %s -P %s" %
                                 (url, CertEnv.datadirectory))

        # Check download file
        if not os.path.exists(white_list):
            return False

        return white_list

    def _get_kernel_source_rpm(self, arch):
        standard_kernel_version = getoutput(
            "dnf list --repo=source | grep kernel.src | head -n 1 | awk '{print $2}'")
        rpmpath = "/root/rpmbuild/SOURCES"
        standard_symvers = os.path.join(rpmpath, "Module.kabi_" + arch)
        if os.path.exists(standard_symvers):
            return standard_symvers

        self.command.run_cmd("dnf download --source kernel-%s" %
                             standard_kernel_version)
        rpm = "kernel-" + standard_kernel_version + ".src.rpm"
        getoutput("rpm -ivh %s" % rpm)
        os.remove(rpm)
        return standard_symvers
