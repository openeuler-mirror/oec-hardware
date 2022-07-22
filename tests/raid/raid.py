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

import os
import sys
import shutil
import argparse
from subprocess import getstatusoutput

from hwcompatible.test import Test
from hwcompatible.command import Command


class RaidTest(Test):
    """
    raid test
    """

    def __init__(self):
        Test.__init__(self)
        self.disks = list()
        self.filesystems = ["ext4"]
        self.device = ""
        self.pci_num = ""
        self.config_data = dict()

    def setup(self, args=None):
        """
        The Setup before testing
        :return:
        """
        self.args = args or argparse.Namespace()
        self.device = getattr(self.args, 'device', None)
        self.pci_num = self.device.get_property("DEVPATH").split('/')[-1]
        self.config_data = getattr(self.args, "config_data", None)
        self.logger = getattr(self.args, "test_logger", None)
        self.log_path = self.logger.logfile
        self.show_driver_info()
        self.logger.info("Vendor Info:", terminal_print=False)
        Command("lspci -s %s -v &>> %s " % (self.pci_num, self.log_path)).echo(ignore_errors=True)
        self.logger.info("Disk Info:", terminal_print=False)
        Command("fdisk -l &>> %s" % self.log_path).echo(ignore_errors=True)
        self.logger.info("Partition Info:", terminal_print=False)
        Command("df -h &>> %s" % self.log_path).echo(ignore_errors=True)
        self.logger.info("Mount Info:", terminal_print=False)
        Command("mount &>> %s" % self.log_path).echo(ignore_errors=True)
        self.logger.info("Swap Info:", terminal_print=False)
        Command("cat /proc/swaps &>> %s" % self.log_path).echo(ignore_errors=True)
        self.logger.info("LVM Info:", terminal_print=False)
        Command("pvdisplay &>> %s" % self.log_path).echo(ignore_errors=True)
        Command("vgdisplay &>> %s" % self.log_path).echo(ignore_errors=True)
        Command("lvdisplay &>> %s" % self.log_path).echo(ignore_errors=True)
        self.logger.info("Md Info:", terminal_print=False)
        Command("cat /proc/mdstat &>> %s" % self.log_path).echo(ignore_errors=True)
        sys.stdout.flush()

    def test(self):
        """
        Start test
        """
        self.get_disk()
        if len(self.disks) == 0:
            self.logger.error("No suite disk found to test.")
            return False

        if not self.config_data:
            self.logger.error("Failed to get disk from configuration file.")
            return False
        disk = self.config_data.get('disk', '')
        result = self.valid_disk(disk, self.disks)
        if not result:
            return False

        return_code = True
        if disk == "all":
            for disk in self.disks:
                if not self.raw_test(disk):
                    return_code = False
                if not self.vfs_test(disk):
                    return_code = False
        else:
            if not self.raw_test(disk):
                return_code = False
            if not self.vfs_test(disk):
                return_code = False
        return return_code

    def get_disk(self):
        """
        Get disk info
        """
        self.disks = list()
        disks = list()
        disk_info = Command("cd /sys/block; ls -l").read().split('\n')
        for disk in disk_info:
            if self.pci_num in disk:
                disks.append(disk.split('/')[-1])

        partition_file = open("/proc/partitions", "r")
        partition = partition_file.read()
        partition_file.close()

        getstatusoutput("/usr/sbin/swapon -a 2> /dev/null")
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

        for disk in disks:
            if disk not in partition or ("/dev/%s" % disk) in swap:
                continue
            if ("/dev/%s" % disk) in mounts or ("/dev/%s" % disk) in mtab:
                continue
            if disk in mdstat or os.system("pvs 2>/dev/null | grep -q '/dev/%s'" % disk) == 0:
                continue
            self.disks.append(disk)

        un_suitable = list(set(disks).difference(set(self.disks)))
        if len(un_suitable) > 0:
            self.logger.info("These disks %s are in use now, skip them." %
                             "|".join(un_suitable))

    def raw_test(self, disk):
        """
        Raw test
        """
        self.logger.info("%s raw IO test" % disk)
        device = os.path.join("/dev", disk)
        if not os.path.exists(device):
            self.logger.error("Device %s does not exist." % device)
        proc_path = os.path.join("/sys/block/", disk)
        if not os.path.exists(proc_path):
            proc_path = os.path.join("/sys/block/*/", disk)
        size = Command("cat %s/size" % proc_path).get_str()
        size = int(size) / 2
        if size <= 0:
            self.logger.error("Device %s size is not suitable for testing." % device)
            return False
        elif size > 1048576:
            size = 1048576

        self.logger.info("Starting sequential raw IO test...")
        opts = "-direct=1 -iodepth 4 -rw=rw -rwmixread=50 -group_reporting -name=file -runtime=300"
        if not self.do_fio(device, size, opts):
            self.logger.info("%s sequential raw IO test failed." % device)
            return False

        self.logger.info("Starting rand raw IO test...")
        opts = "-direct=1 -iodepth 4 -rw=randrw -rwmixread=50 " \
               "-group_reporting -name=file -runtime=300"
        if not self.do_fio(device, size, opts):
            self.logger.error("%s rand raw IO test failed." % device)
            return False

        return True

    def vfs_test(self, disk):
        """
        Vfs test
        """
        self.logger.info("%s vfs test" % disk)
        device = os.path.join("/dev/", disk)
        if not os.path.exists(device):
            self.logger.error("Device %s does not exist." % device)
        proc_path = os.path.join("/sys/block/", disk)
        if not os.path.exists(proc_path):
            proc_path = os.path.join("/sys/block/*/", disk)
        size = Command("cat %s/size" % proc_path).get_str()
        size = int(size) / 2 / 2
        if size <= 0:
            self.logger.error("Device %s size is not suitable for testing." % device)
            return False
        elif size > 1048576:
            size = 1048576

        if os.path.exists("vfs_test"):
            shutil.rmtree("vfs_test")
        os.mkdir("vfs_test")
        path = os.path.join(os.getcwd(), "vfs_test")

        return_code = True
        for file_sys in self.filesystems:
            self.logger.info("Formatting %s to %s ..." % (device, file_sys), terminal_print=False)
            Command("umount %s" % device).echo(ignore_errors=True)
            Command("mkfs -t %s -F %s &>/dev/null" % (file_sys, device)).echo(ignore_errors=True)
            Command("mount -t %s %s %s" % (file_sys, device, "vfs_test")).echo(ignore_errors=True)
            self.logger.info("Starting sequential vfs IO test...")
            opts = "-direct=1 -iodepth 4 -rw=rw -rwmixread=50 -name=directoy -runtime=300"
            if not self.do_fio(path, size, opts):
                return_code = False
                break

            self.logger.info("Starting rand vfs IO test...")
            opts = "-direct=1 -iodepth 4 -rw=randrw -rwmixread=50 -name=directoy -runtime=300"
            if not self.do_fio(path, size, opts):
                return_code = False
                break

        Command("umount %s" % device).echo(ignore_errors=True)
        Command("rm -rf vfs_test").echo(ignore_errors=True)
        return return_code

    def do_fio(self, filepath, size, option):
        """
        Fio test
        """
        if os.path.isdir(filepath):
            file_opt = "-directory=%s" % filepath
        else:
            file_opt = "-filename=%s" % filepath
        max_bs = 64
        a_bs = 4
        while a_bs <= max_bs:
            if getstatusoutput("fio %s -size=%dK -bs=%dK %s &>> %s" %
                               (file_opt, size, a_bs, option, self.log_path))[0] != 0:
                self.logger.error("%s fio failed." % filepath)
                return False
            sys.stdout.flush()
            a_bs = a_bs * 2
        return True
