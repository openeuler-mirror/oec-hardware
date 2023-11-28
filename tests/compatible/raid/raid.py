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
# Create: 2022-04-09
# Desc: Raid test

import argparse
from hwcompatible.command import Command
from hwcompatible.test import Test
from tests.compatible.disk.common import query_disk, get_disk, raw_test, vfs_test, valid_disk


class RaidTest(Test):
    def __init__(self):
        Test.__init__(self)
        self.disks = list()
        self.device = ""
        self.pci_num = ""
        self.requirements = ["fio"]
        self.filesystems = ["ext4"]
        self.config_data = dict()

    def setup(self, args=None):
        self.args = args or argparse.Namespace()
        self.logger = getattr(self.args, "test_logger", None)
        self.command = Command(self.logger)
        self.config_data = getattr(self.args, "config_data", None)

        self.device = getattr(self.args, 'device', None)
        self.pci_num = self.device.get_property("DEVPATH").split('/')[-1]
        self.show_driver_info()
        self.logger.info("Vendor Info:", terminal_print=False)
        self.command.run_cmd("lspci -s %s -v" % self.pci_num)
        query_disk(self.logger, self.command)

    def test(self):
        """
        Start test
        """
        self.disks = get_disk(self.logger, self.command, self.config_data, self.pci_num)
        if len(self.disks) == 0:
            self.logger.error("No suite disk found to test.")
            return False

        disk = self.config_data.get('disk', '')
        if not valid_disk(self.logger, disk, self.disks):
            return False

        return_code = True
        if disk != "all":
            self.disks = [disk]
        for disk in self.disks:
            if not raw_test(self.logger, self.command, disk):
                return_code = False
            if not vfs_test(self.logger, self.command, disk, self.filesystems):
                return_code = False
        return return_code
