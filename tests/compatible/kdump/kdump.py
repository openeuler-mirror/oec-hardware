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
# Desc: Kdump Test

import os
import re
from time import sleep
from subprocess import getoutput
from hwcompatible.test import Test
from hwcompatible.command import Command
from hwcompatible.command_ui import CommandUI
from hwcompatible.document import ConfigFile


class KdumpTest(Test):
    def __init__(self):
        Test.__init__(self)
        self.pri = 9
        self.reboot = True
        self.kernel_version = getoutput("uname -r")
        self.rebootup = "verify_vmcore"
        self.kdump_conf = "/etc/kdump.conf"
        self.vmcore_path = "/var/crash"
        self.requirements = ["crash", "kexec-tools"]

    def test(self):
        """
        Test case
        :return:
        """
        cmd_result = self.command.run_cmd("yum install -y kernel-debuginfo-%s" % self.kernel_version)
        if len(cmd_result[1]) != 0 and cmd_result[2] != 0:
            self.logger.error(
                "Fail to install required packages.\n %s" % cmd_result[1])
            return False

        cmd_result = self.command.run_cmd("grep crashkernel /proc/cmdline")
        if cmd_result[2] != 0:
            self.logger.error(
                "The /proc/cmdline file cannot find crashkernel.")
            return False
        crash_kernel = cmd_result[0].split(" ")
        crash_size = ""
        for line in crash_kernel:
            if "crashkernel" in line:
                crash_size = line.split("=")[1]
                break
        self.logger.info("The value of crashkernel is %s" % crash_size)

        config = ConfigFile(self.kdump_conf)
        if not config.get_parameter("path"):
            config.add_parameter("path", self.vmcore_path)
        else:
            self.vmcore_path = config.get_parameter("path")

        if config.get_parameter("kdump_obj") == "kbox":
            config.remove_parameter("kdump_obj")
            config.add_parameter("kdump_obj", "all")

        self.command.run_cmd("systemctl restart kdump")
        cmd = self.command.run_cmd(
            "systemctl status kdump | grep 'Active: active'")
        if cmd[2] != 0:
            self.logger.error("Kdump service is not active.")
            return False
        self.logger.info("Start kdump service succeed.")

        self.logger.info("kdump config.")
        config.dump()

        com_ui = CommandUI()
        if com_ui.prompt_confirm("System will reboot, are you ready?"):
            self.logger.info("Trigger crash, please wait seconds.")
            self.command.run_cmd("sync", log_print=False)
            self.command.run_cmd("echo 'c' | tee /proc/sysrq-trigger")
            sleep(30)
            return False

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
        for (_, dirs, _) in os.walk(self.vmcore_path):
            for eve_dir in dirs:
                if dir_pattern.search(eve_dir):
                    vmcore_dirs.append(eve_dir)
        vmcore_dirs.sort()
        vmcore_file = os.path.join(self.vmcore_path, vmcore_dirs[-1], "vmcore")
        command = Command(logger)
        cmd = command.run_cmd(
            "echo 'sys\nq'| crash -s %s /usr/lib/debug/lib/modules/%s/vmlinux" % (vmcore_file, self.kernel_version))
        if cmd[2] == 0:
            logger.info("Verify kdump image %s succeed." % vmcore_file)
            return True
        logger.error("Verify kdump image %s failed." % vmcore_file)
        return False
