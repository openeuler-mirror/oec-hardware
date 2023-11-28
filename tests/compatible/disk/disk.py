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
# Desc: Disk test

import argparse
from hwcompatible.test import Test
from hwcompatible.command import Command
from common import query_disk, get_disk, raw_test, vfs_test, valid_disk


class DiskTest(Test):
    def __init__(self):
        Test.__init__(self)
        self.disks = list()
        self.requirements = ["fio"]
        self.filesystems = ["ext4"]
        self.config_data = ""

    def setup(self, args=None):
        """
        The Setup before testing
        :return:
        """
        self.args = args or argparse.Namespace()
        self.logger = getattr(self.args, "test_logger", None)
        self.command = Command(self.logger)
        self.config_data = getattr(self.args, "config_data", None)
        query_disk(self.logger, self.command)

    def test(self):
        """
        Start test
        """
        self.disks = get_disk(self.logger, self.command, self.config_data)
        if len(self.disks) == 0:
            self.logger.error("No suite disk found to test.")
            return False

        if not self.config_data:
            self.logger.error("Failed to get disk from configuration file.")
            return False
        disk = self.config_data
        result = valid_disk(self.logger, disk, self.disks)
        if not result:
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
