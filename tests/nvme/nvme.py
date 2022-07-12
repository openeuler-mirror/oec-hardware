#!/usr/bin/env python3
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
        self.device = getattr(args, "device", None)
        self.name = self.device.get_name()
        self.logpath = os.path.join(getattr(self.args, "logdir", None), "nvme-" + self.name + ".log")
        self.show_driver_info()
        Command("nvme list").echo(ignore_errors=True)

    def test(self):
        """
        test case
        :return:
        """
        disk = self.device.get_name()
        if self.in_use(disk):
            print("%s is in use now, skip this test." % disk)
            return False

        size = Command("cat /sys/block/%s/size" % disk).get_str()
        size = int(int(size))/2/2
        if size <= 0:
            print("Error: the size of %s is not suitable for this test." % disk)
            return False
        elif size > 10*1024*1014*1024:
            size = 10*1024*1014*1024

        try:
            print("\nFormatting...")
            Command("nvme format -l 0 -i 0 /dev/%s" % disk).echo()
            sys.stdout.flush()

            print("\nWritting...")
            Command("nvme write -z %d -s 0 -d /dev/urandom /dev/%s 2> /dev/null" \
                    % (size, disk)).echo()
            sys.stdout.flush()

            print("\nReading...")
            Command("nvme read -s 0 -z %d /dev/%s &> /dev/null" % (size, disk)).echo()
            sys.stdout.flush()

            print("\nSmart Log:")
            Command("nvme smart-log /dev/%s 2> /dev/null" % disk).echo()
            sys.stdout.flush()

            print("\nLog:")
            Command("nvme get-log -i 1 -l 128 /dev/%s 2> /dev/null" % disk).echo()
            print("")
            sys.stdout.flush()

            Command("nvme list").echo(ignore_errors=True)
            return True
        except Exception as concrete_error:
            print("Error: nvme cmd fail.")
            print(concrete_error)
            return False

    def in_use(self, disk):
        """
        Determine whether the swapon is in use
        :param disk:
        :return:
        """
        os.system("swapon -a 2>/dev/null")
        swap_file = open("/proc/swaps", "r")
        swap = swap_file.read()
        swap_file.close()

        mdstat_file = open("/proc/mdstat", "r")
        mdstat = mdstat_file.read()
        mdstat_file.close()

        mtab_file = open("/etc/mtab", "r")
        mtab = mtab_file.read()
        mtab_file.close()

        mount_file = open("/proc/mounts", "r")
        mounts = mount_file.read()
        mount_file.close()

        if ("/dev/%s" % disk) in swap or disk in mdstat:
            return True
        if ("/dev/%s" % disk) in mounts or ("/dev/%s" % disk) in mtab:
            return True
        if os.system("pvs 2>/dev/null | grep -q '/dev/%s'" % disk) == 0:
            return True
