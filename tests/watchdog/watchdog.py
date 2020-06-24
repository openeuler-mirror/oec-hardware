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
from hwcompatible.command import Command, CertCommandError


class WatchDogTest(Test):

    def __init__(self):
        Test.__init__(self)
        self.pri = 9
        self.reboot = True
        self.rebootup = "startup"
        self.max_timeout = 20
        self.test_dir = os.path.dirname(os.path.realpath(__file__))

    def test(self):
        if not os.path.exists("/dev/watchdog"):
            os.system("modprobe softdog")

        os.chdir(self.test_dir)
        try:
            timeout = Command("./watchdog -g").get_str(regex="^Watchdog timeout is (?P<timeout>[0-9]*) seconds.$",regex_group="timeout")
            timeout = int(timeout)
            if timeout > self.max_timeout:
                Command("./watchdog -s %d" % self.max_timeout).echo()
        except Exception as e:
            print(e)
            print("Set/get watchdog timeout failed.")
            return False

        ui = CommandUI()
        if ui.prompt_confirm("System will reboot, are you ready?"):
            print("")
            sys.stdout.flush()
            os.system("sync")
            os.system("./watchdog -t")
            time.sleep(5)
            return False
        else:
            print("")
            return False

    @staticmethod
    def startup():
        print("Recover from watchdog.")
        return True
