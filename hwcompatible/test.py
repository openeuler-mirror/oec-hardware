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
# Desc: Test template

import os
from .device import Device
from .command import Command


class Test:
    """
    Test template
    """

    def __init__(self):
        self.pri = 0
        self.requirements = list()
        self.reboot = False
        self.rebootup = None
        self.args = None
        self.logger = None

    @staticmethod
    def valid_disk(disk, disks):
        """
        Is the disk valid
        """
        result = True
        if disk:
            if disk != "all" and disk not in disks:
                print("%s is in use or disk does not exist." % disk)
                result = False
        else:
            print("Failed to get disk information.")
            result = False
        return result

    def setup(self, args=None):
        """
        setup
        """
        pass

    def show_driver_info(self):
        """
        show driver name and driver version
        """
        driver_name = self.device.get_driver()
        driver_version = self.device.get_driver_version()
        Command("echo Driver Name: %s >> %s" % (driver_name, self.logpath)).echo()
        if not driver_version:
            print("The driver version information cannot be obtained. Please view it manually.")
        else:
            Command("echo Driver Version: %s >> %s" % (driver_version, self.logpath)).echo()

    def teardown(self):
        """
        teardown
        """
        pass