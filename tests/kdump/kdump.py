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

import os
import sys
import time
import re

from hwcompatible.test import Test
from hwcompatible.command_ui import CommandUI
from hwcompatible.document import ConfigFile
from hwcompatible.command import Command, CertCommandError


class KdumpTest(Test):
    """
    Kdump Test
    """

    def __init__(self):
        Test.__init__(self)
        self.pri = 9
        self.reboot = True
        self.rebootup = "verify_vmcore"
        self.kdump_conf = "/etc/kdump.conf"
        self.vmcore_path = "/var/crash"
        self.requirements = ["crash", "kernel-debuginfo", "kexec-tools"]

    def test(self):
        """
        Test case
        :return:
        """
        try:
            crash_kernel = Command("cat /proc/cmdline").get_str(r"crashkernel=[^\ ]*")
            self.logger.info("The value of Crashkernel is %s", crash_kernel)
        except Exception:
            self.logger.error("Crashkernel not found.")
            return False

        config = ConfigFile(self.kdump_conf)
        if not config.get_parameter("path"):
            config.add_parameter("path", self.vmcore_path)
        else:
            self.vmcore_path = config.get_parameter("path")

        if config.get_parameter("kdump_obj") == "kbox":
            config.remove_parameter("kdump_obj")
            config.add_parameter("kdump_obj", "all")

        self.logger.info("Start kdump service")
        try:
            Command("systemctl restart kdump &>> %s" % self.logger.logfile).run()
            Command("systemctl status kdump &>> %s" % self.logger.logfile).get_str\
                (regex="Active: active", single_line=False)
        except Exception:
            self.logger.error("Kdump service is not activated.")
            return False
        self.logger.info("Start kdump service succeed")

        self.logger.info("kdump config")
        config.dump()

        com_ui = CommandUI()
        if com_ui.prompt_confirm("System will reboot, are you ready?"):
            self.logger.info("trigger crash...")
            sys.stdout.flush()
            os.system("sync")
            os.system("echo c > /proc/sysrq-trigger")
            time.sleep(30)
            return False
        else:
            return False

    def verify_vmcore(self, logger):
        """
        Verify vmcore
        :return:
        """
        config = ConfigFile(self.kdump_conf)
        if config.get_parameter("path"):
            self.vmcore_path = config.get_parameter("path")

        dir_pattern = re.compile(
            r'(?P<ipaddr>[0-9]+\.[0-9]+\.[0-9]+)-(?P<date>[0-9]+[-.][0-9]+[-.][0-9]+)-'
            r'(?P<time>[0-9]+:[0-9]+:[0-9]+)')

        vmcore_dirs = list()
        for (root, dirs, files) in os.walk(self.vmcore_path):
            for eve_dir in dirs:
                if dir_pattern.search(eve_dir):
                    vmcore_dirs.append(eve_dir)
        vmcore_dirs.sort()
        vmcore_file = os.path.join(self.vmcore_path, vmcore_dirs[-1], "vmcore")

        try:
            Command(
                "echo \"sys\nq\" | crash -s %s /usr/lib/debug/lib/modules/`uname -r`/vmlinux &>> %s"
                % (vmcore_file, logger.logfile)).echo()
            logger.info("Kdump image %s verified" % vmcore_file)
            return True
        except CertCommandError as concrete_error:
            logger.error("Could not verify kdump image %s" % vmcore_file)
            logger.error(concrete_error)
            return False
