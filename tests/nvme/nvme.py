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

"""Test Non-Volatile Memory express"""

import os
import sys
import argparse
from hwcompatible.test import Test
from hwcompatible.command import Command


class NvmeTest(Test):
    """
    Test Non-Volatile Memory express
    """
    def __init__(self):
        Test.__init__(self)
        self.requirements = ["nvme-cli"]
        self.args = None
        self.device = None
        self.name = ""
        self.logpath = ""

    def setup(self, args=None):
        """
        Initialization before test
        :param args:
        :return:
        """
        self.args = args or argparse.Namespace()
        self.logger = getattr(args, "test_logger", None)
        self.log_path = self.logger.logfile
        self.device = getattr(args, "device", None)
        self.show_driver_info()
        Command("nvme list &>> %s" % self.log_path).echo(ignore_errors=True)

    def test(self):
        """
        test case
        :return:
        """
        disk = self.device.get_name()
        if self.in_use(disk):
            self.logger.error("%s is in use now, skip this test." % disk)
            return False

        size = Command("cat /sys/block/%s/size" % disk).get_str()
        size = int(int(size))/2/2
        if size <= 0:
            self.logger.error("The size of %s is not suitable for this test." % disk)
            return False
        elif size > 10*1024*1014*1024:
            size = 10*1024*1014*1024

        try:
            self.logger.info("Formatting...")
            Command("nvme format -l 0 -i 0 /dev/%s &>> %s" % (disk, self.log_path)).echo()
            sys.stdout.flush()

            self.logger.info("Writting...")
            Command("nvme write -z %d -s 0 -d /dev/urandom /dev/%s 2> /dev/null" %
                    (size, disk)).echo()
            sys.stdout.flush()

            self.logger.info("Reading...")
            Command("nvme read -s 0 -z %d /dev/%s &> /dev/null" % (size, disk)).echo()
            sys.stdout.flush()

            self.logger.info("\nSmart Log:")
            Command("nvme smart-log /dev/%s 2> /dev/null" % disk).echo()
            sys.stdout.flush()

            self.logger.info("\nLog:")
            Command("nvme get-log -i 1 -l 128 /dev/%s 2> /dev/null" % disk).echo()
            sys.stdout.flush()

            Command("nvme list &>> %s" % self.log_path).echo(ignore_errors=True)
            return True
        except Exception as concrete_error:
            self.logger.error("Nvme cmd fail.")
            self.logger.error(concrete_error)
            return False

    def in_use(self, disk):
        """
        Determine whether the swapon is in use
        :param disk:
        :return:
        """
        Command("swapon -a 2>/dev/null").echo()
        with open("/proc/swaps", "r") as swap_file:
            swap = swap_file.read()

        with open("/proc/mdstat", "r") as mdstat_file:
            mdstat = mdstat_file.read()

        with open("/etc/mtab", "r") as mtab_file:
            mtab = mtab_file.read()

        with open("/proc/mounts", "r") as mount_file:
            mounts = mount_file.read()

        if ("/dev/%s" % disk) in swap or disk in mdstat:
            return True
        if ("/dev/%s" % disk) in mounts or ("/dev/%s" % disk) in mtab:
            return True
        if os.system("pvs 2>/dev/null | grep -q '/dev/%s'" % disk) == 0:
            return True
