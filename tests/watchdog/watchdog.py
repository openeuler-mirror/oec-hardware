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
import time
from hwcompatible.test import Test
from hwcompatible.command_ui import CommandUI


class WatchDogTest(Test):
    """
    WatchDog Test
    """

    def __init__(self):
        Test.__init__(self)
        self.pri = 9
        self.reboot = True
        self.rebootup = "startup"
        self.max_timeout = 20
        self.test_dir = os.path.dirname(os.path.realpath(__file__))

    def test(self):
        """
        test case
        :return:
        """
        self.logger.info("Load softdog driver.")
        if not os.path.exists("/dev/watchdog"):
            self.command.run_cmd("modprobe softdog")

        self.logger.info("Set/Get the watchdog timeout time.")
        os.chdir(self.test_dir)
        result = self.command.run_cmd(
            "./watchdog -g | grep '^Watchdog timeout is *'")
        if result[2] != 0:
            self.logger.error("Execute watchdog -g failed.")
            return False
        timeout = int(result[0].split(" ")[3])
        if timeout > self.max_timeout:
            self.command.run_cmd("./watchdog -s %d" % self.max_timeout)
        self.logger.info("Set/Get watchdog timeout succeed.")

        ui = CommandUI()
        if ui.prompt_confirm("System will reboot, are you ready?"):
            self.logger.info("Please wait seconds.")
            self.command.run_cmd("sync", log_print=False)
            self.command.run_cmd("./watchdog -t", log_print=False)
            time.sleep(5)
            return False
        else:
            return False

    def startup(self, logger):
        """
        Initialization before test
        :return:
        """
        logger.info("Recover from watchdog.")
        return True
