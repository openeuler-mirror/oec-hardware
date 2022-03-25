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


"""disk test"""

import os
import sys
import shutil

from hwcompatible.test import Test
from hwcompatible.command import Command, CertCommandError
from hwcompatible.commandUI import CommandUI
from hwcompatible.device import CertDevice

class DiskTest(Test):
    """
    disk test
    """

    def __init__(self):
        Test.__init__(self)
        self.disks = list()
        self.filesystems = ["ext4"]
        self.com_ui = CommandUI()
        self.logpath = ""

    def setup(self, args=None):
        """
        The Setup before testing
        :return:
        """
        try:
            self.args = args or argparse.Namespace()
            self.logpath = getattr(args, "logdir", None) + "/disk.log"
            os.system("echo 'Disk Info: ' >> %s" % self.logpath)
            Command("fdisk -l &>> %s" % self.logpath).echo(ignore_errors=True)
            os.system("echo 'Partition Info: ' >> %s" % self.logpath)
            Command("df -h &>> %s" % self.logpath).echo(ignore_errors=True)
            os.system("echo 'Mount Info: ' >> %s" % self.logpath)
            Command("mount &>> %s" % self.logpath).echo(ignore_errors=True)
            os.system("echo 'Swap Info: ' >> %s" % self.logpath)
            Command("cat /proc/swaps &>> %s" %
                    self.logpath).echo(ignore_errors=True)
            os.system("echo 'LVM Info: ' >> %s" % self.logpath)
            Command("pvdisplay &>> %s" % self.logpath).echo(ignore_errors=True)
            Command("vgdisplay &>> %s" % self.logpath).echo(ignore_errors=True)
            Command("lvdisplay &>> %s" % self.logpath).echo(ignore_errors=True)
            os.system("echo 'Md Info: ' >> %s" % self.logpath)
            Command("cat /proc/mdstat &>> %s" %
                    self.logpath).echo(ignore_errors=True)
            sys.stdout.flush()
        except Exception as concrete_error:
            print("Warning: could not get disk info.\n", concrete_error)

    def test(self):
        """
        start test
        """
        self.get_disk()
        if len(self.disks) == 0:
            print("No suite disk found to test.")
            return False

        self.disks.append("all")
        disk = self.com_ui.prompt_edit("Which disk would you like to test: ",
                                       self.disks[0], self.disks)
        return_code = True
        if disk == "all":
            for disk in self.disks[:-1]:
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
        get disk info
        """
        self.disks = list()
        disks = list()
        devices = CertDevice().get_devices()
        for device in devices:
            if (device.get_property("DEVTYPE") == "disk" and not
                    device.get_property("ID_TYPE")) or device.\
                    get_property("ID_TYPE") == "disk":
                if "/host" in device.get_property("DEVPATH"):
                    disks.append(device.get_name())

        partition_file = open("/proc/partitions", "r")
        partition = partition_file.read()
        partition_file.close()

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
            print("These disks %s are in use now, skip them." %
                  "|".join(un_suitable))

    def raw_test(self, disk):
        """
        raw test
        """
        print("\n#############")
        print("%s raw IO test" % disk)
        device = "/dev/" + disk
        if not os.path.exists(device):
            print("Error: device %s not exists." % device)
        proc_path = "/sys/block/" + disk
        if not os.path.exists(proc_path):
            proc_path = "/sys/block/*/" + disk
        size = Command("cat %s/size" % proc_path).get_str()
        size = int(size)/2
        if size <= 0:
            print("Error: device %s size not suitable to do test." % device)
            return False
        elif size > 1048576:
            size = 1048576

        print("\nStarting sequential raw IO test...")
        opts = "-direct=1 -iodepth 4 -rw=rw -rwmixread=50 -group_reporting -name=file -runtime=300"
        if not self.do_fio(device, size, opts):
            print("%s sequential raw IO test fail." % device)
            print("#############")
            return False

        print("\nStarting rand raw IO test...")
        opts = "-direct=1 -iodepth 4 -rw=randrw -rwmixread=50 " \
               "-group_reporting -name=file -runtime=300"
        if not self.do_fio(device, size, opts):
            print("%s rand raw IO test fail." % device)
            print("#############")
            return False

        print("#############")
        return True

    def vfs_test(self, disk):
        """
        vfs test
        """
        print("\n#############")
        print("%s vfs test" % disk)
        device = "/dev/" + disk
        if not os.path.exists(device):
            print("Error: device %s not exists." % device)
        proc_path = "/sys/block/" + disk
        if not os.path.exists(proc_path):
            proc_path = "/sys/block/*/" + disk
        size = Command("cat %s/size" % proc_path).get_str()
        size = int(size)/2/2
        if size <= 0:
            print("Error: device %s size not suitable to do test." % device)
            return False
        elif size > 1048576:
            size = 1048576

        if os.path.exists("vfs_test"):
            shutil.rmtree("vfs_test")
        os.mkdir("vfs_test")
        path = os.path.join(os.getcwd(), "vfs_test")

        return_code = True
        for file_sys in self.filesystems:
            try:
                print("\nFormatting %s to %s ..." % (device, file_sys))
                Command("umount %s" % device).echo(ignore_errors=True)
                Command("mkfs -t %s -F %s &>/dev/null" %
                        (file_sys, device)).echo()
                Command("mount -t %s %s %s" %
                        (file_sys, device, "vfs_test")).echo()

                print("\nStarting sequential vfs IO test...")
                opts = "-direct=1 -iodepth 4 -rw=rw -rwmixread=50 -name=directoy -runtime=300"
                if not self.do_fio(path, size, opts):
                    return_code = False
                    break

                print("\nStarting rand vfs IO test...")
                opts = "-direct=1 -iodepth 4 -rw=randrw -rwmixread=50 -name=directoy -runtime=300"
                if not self.do_fio(path, size, opts):
                    return_code = False
                    break
            except Exception as concrete_error:
                print(concrete_error)
                return_code = False
                break

        Command("umount %s" % device).echo(ignore_errors=True)
        Command("rm -rf vfs_test").echo(ignore_errors=True)
        print("#############")
        return return_code

    def do_fio(self, filepath, size, option):
        """
        fio test
        """
        if os.path.isdir(filepath):
            file_opt = "-directory=%s" % filepath
        else:
            file_opt = "-filename=%s" % filepath
        max_bs = 64
        a_bs = 4
        while a_bs <= max_bs:
            if os.system("fio %s -size=%dK -bs=%dK %s &>> %s" % (file_opt, size, a_bs, option, self.logpath)) != 0:
                print("Error: %s fio failed." % filepath)
                return False
            sys.stdout.flush()
            a_bs = a_bs * 2
        return True
