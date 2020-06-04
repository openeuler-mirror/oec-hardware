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
import time
import re
from hwcompatible.test import Test
from hwcompatible.commandUI import CommandUI
from hwcompatible.document import ConfigFile
from hwcompatible.command import Command, CertCommandError


class KdumpTest(Test):

    def __init__(self):
        Test.__init__(self)
        self.pri = 9
        self.reboot = True
        self.rebootup = "verify_vmcore"
        self.kdump_conf = "/etc/kdump.conf"
        self.vmcore_path = "/var/crash"
        self.requirements = ["crash", "kernel-debuginfo", "kexec-tools"]

    def test(self):
        try:
            Command("cat /proc/cmdline").get_str("crashkernel=[^\ ]*")
        except:
            print("Error: no crashkernel found.")
            return False

        config = ConfigFile(self.kdump_conf)
        if not config.get_parameter("path"):
            config.add_parameter("path", self.vmcore_path)
        else:
            self.vmcore_path = config.get_parameter("path")

        if config.get_parameter("kdump_obj") == "kbox":
            config.remove_parameter("kdump_obj")
            config.add_parameter("kdump_obj", "all")

        try:
            Command("systemctl restart kdump").run()
            Command("systemctl status kdump").get_str(regex="Active: active", single_line=False)
        except:
            print("Error: kdump service not working.")
            return False

        print("kdump config:")
        print("#############")
        config.dump()
        print("#############")

        ui = CommandUI()
        if ui.prompt_confirm("System will reboot, are you ready?"):
            print("\ntrigger crash...")
            sys.stdout.flush()
            os.system("sync")
            os.system("echo c > /proc/sysrq-trigger")
            time.sleep(30)
            return False
        else:
            print("")
            return False

    def verify_vmcore(self):
        config = ConfigFile(self.kdump_conf)
        if config.get_parameter("path"):
            self.vmcore_path = config.get_parameter("path")

        dir_pattern = re.compile("(?P<ipaddr>[0-9]+\.[0-9]+\.[0-9]+)-(?P<date>[0-9]+(-|\.)[0-9]+(-|\.)[0-9]+)-(?P<time>[0-9]+:[0-9]+:[0-9]+)")
        vmcore_dirs = list()
        for (root, dirs, files) in os.walk(self.vmcore_path):
            for dir in dirs:
                if dir_pattern.search(dir):
                    vmcore_dirs.append(dir)
        vmcore_dirs.sort()
        vmcore_file = os.path.join(self.vmcore_path, vmcore_dirs[-1], "vmcore")

        try:
            Command("echo \"sys\nq\" | crash -s %s /usr/lib/debug/lib/modules/`uname -r`/vmlinux" % vmcore_file).echo()
            print("kdump image %s verified" % vmcore_file)
            return True
        except CertCommandError as e:
            print("Error: could not verify kdump image %s" % vmcore_file)
            print(e)
            return False

