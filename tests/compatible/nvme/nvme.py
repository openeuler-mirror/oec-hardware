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
# Desc: Test Non-Volatile Memory express

import os
import argparse
import json
from subprocess import getoutput
from hwcompatible.test import Test
from hwcompatible.command import Command


class NvmeTest(Test):
    def __init__(self):
        Test.__init__(self)
        self.requirements = ["nvme-cli"]
        self.args = None
        self.device = None
        self.filename = "test.file"
        self.logpath = ""

    def setup(self, args=None):
        """
        Initialization before test
        :param args:
        :return:
        """
        self.args = args or argparse.Namespace()
        self.logger = getattr(args, "test_logger", None)
        self.command = Command(self.logger)
        self.device = getattr(args, "device", None)
        self.show_driver_info()
        self.command.run_cmd("nvme list", ignore_errors=True)

    def test(self):
        """
        test case
        :return:
        """
        disk = self.device.get_name()
        if self.in_use(disk):
            self.logger.error("%s is in use now, skip this test." % disk)
            return False

        block_count = getoutput("cat /sys/block/%s/size" % disk)
        block_size = getoutput("cat /sys/block/%s/queue/logical_block_size" % disk)
        size = int(block_count) * int(block_size)
        size = size / 2 / 2
        if size <= 0:
            self.logger.error(
                "The size of %s is not suitable for this test." % disk)
            return False
        elif size > 128 * 1024:
            size = 128 * 1024

        nvme_info = json.loads(self.command.run_cmd("nvme list -o json")[0], strict=False)["Devices"]
        for nvme in nvme_info:
            if nvme["DevicePath"] == os.path.join("/dev/", disk):
                size_per_block = int(nvme["SectorSize"])
                break

        block_num = 1
        if size_per_block != 0:
            block_num = int(int(size) / size_per_block) - 1

        cmd = "seq -s a 150000 | tee %s" % self.filename
        result = self.command.run_cmd(cmd, log_print=False)
        if result[2] != 0:
            self.logger.error("Create file failed!")
            return False

        self.logger.info("Start to format nvme.")
        return_code = True
        cmd_list = [
            "nvme format -l 0 -i 0 /dev/%s" % disk,
            "nvme write -c %d -s 0 -z %d -d %s /dev/%s" % (block_num, size, self.filename, disk),
            "nvme read -c %d -s 0 -z %d /dev/%s" % (block_num, size, disk),
            "nvme smart-log /dev/%s" % disk,
            "nvme get-log -i 1 -l 128 /dev/%s" % disk
        ]
        for cmd in cmd_list:
            result = self.command.run_cmd(cmd)
            if result[2] != 0:
                return_code = False

        self.command.run_cmd("nvme list", ignore_errors=True)
        if return_code:
            self.logger.info("Test nvme succeed.")
        else:
            self.logger.info("Test nvme failed.")
        return return_code

    def in_use(self, disk):
        """
        Determine whether the swapon is in use
        :param disk:
        :return:
        """
        self.command.run_cmd("/usr/sbin/swapon -a")
        with open("/proc/swaps", "r") as swap_file:
            swap = swap_file.read()

        with open("/proc/mdstat", "r") as mdstat_file:
            mdstat = mdstat_file.read()

        with open("/proc/mounts", "r") as mount_file:
            mounts = mount_file.read()

        if ("/dev/%s" % disk) in swap or disk in mdstat:
            return True

        if ("/dev/%s" % disk) in mounts:
            return True

        result = self.command.run_cmd("pvs | grep -q '/dev/%s'" % disk)
        if result[2] == 0:
            return True

        return False

    def teardown(self):
        """
        Environment recovery
        """
        if os.path.exists(self.filename):
            os.remove(self.filename)
