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
# Desc: CDRom test

import os
import shutil
import argparse
from time import sleep
from hwcompatible.test import Test
from hwcompatible.command_ui import CommandUI
from hwcompatible.command import Command


class CDRomTest(Test):
    def __init__(self):
        Test.__init__(self)
        self.requirements = ["dvd+rw-tools",
                             "cdrkit", "genisoimage", "util-linux"]
        self.method = None
        self.device = None
        self.type = None
        self.com_ui = CommandUI()
        self.test_dir = "/usr/share/doc"
        read_dir = os.getcwd()
        self.mnt_dir = os.path.join(read_dir, "mnt_cdrom")
        self.device_dir = os.path.join(read_dir, "device_dir")

    def setup(self, args=None):
        """
        The Setup before testing
        :param args:
        :return:
        """
        self.args = args or argparse.Namespace()
        self.logger = getattr(args, "test_logger", None)
        self.device = getattr(args, "device", None)
        self.type = self.get_type(self.device)
        self.command = Command(self.logger)
        self.get_mode(self.type)

    def test(self):
        """
        Test case
        :return:
        """
        if not (self.method and self.device and self.type):
            return False

        if self.method not in dir(self):
            return False

        devname = self.device.get_property("DEVNAME")
        self.command.run_cmd("eject %s" % devname, ignore_errors=True)
        while True:
            self.logger.info("Please insert %s disc into %s, then close the tray manually." % (
                self.type.lower(), devname))
            if self.method == "write_test":
                self.logger.info("Tips: disc should be new.")
            elif self.method == "read_test":
                self.logger.info("Tips: disc should not be blank.")
            if self.com_ui.prompt_confirm("Done well?"):
                break
        self.command.run_cmd("eject -t %s" % devname, ignore_errors=True)
        self.logger.info(
            "Please wait seconds for media to be inserted.", terminal_print=True)
        sleep(20)

        if not getattr(self, self.method)():
            return False
        return True

    def get_type(self, device):
        """
        Get the type of CDROM
        :param device:
        :return:
        """
        if not device:
            return None

        bd_types = ["BD_RE", "BD_R", "BD"]
        dvd_types = ["DVD_RW", "DVD_PLUS_RW", "DVD_R", "DVD_PLUS_R", "DVD"]
        cd_types = ["CD_RW", "CD_R", "CD"]
        for bd_type in bd_types:
            if device.get_property("ID_CDROM_" + bd_type) == "1":
                return bd_type
        for dvd_type in dvd_types:
            if device.get_property("ID_CDROM_" + dvd_type) == "1":
                return dvd_type
        for cd_type in cd_types:
            if device.get_property("ID_CDROM_" + cd_type) == "1":
                return cd_type

        self.logger.error("Find proper test-type for %s failed." %
                          device.get_name())
        return None

    def get_mode(self, device_type):
        """
        Get the read-write mode of CDROM
        :param device_type:
        :return:
        """
        if not device_type:
            return

        if "RW" in device_type or "RE" in device_type:
            self.method = "rw_test"
        elif "_R" in device_type:
            self.method = "write_test"
        else:
            self.method = "read_test"

    def rw_test(self):
        """
        RW mode test of CDROM
        :return:
        """
        devname = self.device.get_property("DEVNAME")
        self.command.run_cmd("umount %s" % devname, ignore_errors=True)
        if "BD" in self.type:
            self.logger.info("It will format the cdrom.", terminal_print=True)
            self.command.run_cmd("dvd+rw-format -format=full %s" % devname)
            self.reload_disc(devname)
            return self.write_test()
        elif "DVD_PLUS" in self.type:
            self.logger.info("It will format the cdrom.", terminal_print=True)
            self.command.run_cmd("dvd+rw-format -force %s" % devname)
            self.reload_disc(devname)
            return self.write_test()
        else:
            self.logger.info("It will clear data in cdrom.",
                             terminal_print=True)
            self.command.run_cmd("cdrecord -v dev=%s blank=fast" % devname)
            self.reload_disc(devname)
            return self.write_test()

    def write_test(self):
        """
        Write mode test of CDROM
        :return:
        """
        devname = self.device.get_property("DEVNAME")
        self.command.run_cmd("umount %s" % devname, ignore_errors=True)
        if "BD" in self.type or "DVD_PLUS" in self.type:
            grow_cmd = self.command.run_cmd(
                "growisofs -Z %s --quiet -R %s " % (devname, self.test_dir))
            reload_flag = self.reload_disc(devname)
            if grow_cmd[2] == 0 and reload_flag:
                return True
            return False

        write_opts = "-sao"
        cmd_result = self.command.run_cmd(
            "cdrecord dev=%s -checkdrive | grep 'Supported modes'" % devname, ignore_errors=True)
        modes = cmd_result[0]
        if "TAO" in modes:
            write_opts = "-tao"
        if "SAO" in modes:
            write_opts = "-sao"
        cmd_result = self.command.run_cmd(
            "cdrecord dev=%s -checkdrive | grep 'Driver flags'" % devname, ignore_errors=True)
        if "BURNFREE" in cmd_result[0]:
            write_opts += " driveropts=burnfree"

        size = self.command.run_cmd(
            "mkisofs -quiet -R -print-size %s" % self.test_dir)
        blocks = int(size[0])

        self.command.run_cmd(
            "mkisofs -o test_cdrom.iso --quiet -r %s" % self.test_dir)
        mkisofs_cmd = self.command.run_cmd(
            "cdrecord -v %s dev=%s fs=32M test_cdrom.iso" % (write_opts, devname))
        reload_flag = self.reload_disc(devname)
        os.remove("test_cdrom.iso")
        if mkisofs_cmd[2] == 0 and reload_flag:
            return True
        return False

    def read_test(self):
        """
        Read mode test of CDROM
        :return:
        """
        devname = self.device.get_property("DEVNAME")
        if os.path.exists(self.mnt_dir):
            shutil.rmtree(self.mnt_dir)
        os.mkdir(self.mnt_dir)
        self.logger.info("Check to mount media.", terminal_print=True)
        self.command.run_cmd("umount %s" % devname, ignore_errors=True)
        self.command.run_cmd("mount -o ro %s %s" % (devname, self.mnt_dir))

        cmd_result = self.command.run_cmd(
            "df %s | tail -n1 | awk '{print $3}'" % devname)
        size = int(cmd_result[0])
        if size == 0:
            self.logger.error("This is a blank disc.")
            self.command.run_cmd("umount %s" % self.mnt_dir)
            shutil.rmtree(self.mnt_dir)
            return False

        if os.path.exists(self.device_dir):
            shutil.rmtree(self.device_dir)
        os.mkdir(self.device_dir)
        self.logger.info("Check to copy files.", terminal_print=True)
        self.command.run_cmd("cp -dprf %s/. %s" % (self.mnt_dir, self.device_dir))

        self.logger.info(
            "Check to compare files in directory.", terminal_print=True)
        return_code = self.cmp_tree(self.mnt_dir, self.device_dir)
        self.command.run_cmd("umount %s" % self.mnt_dir)
        if return_code:
            self.logger.info("Compare directory succeed.")
        else:
            self.logger.error("Compare directory failed.")

        return return_code

    def cmp_tree(self, dir1, dir2):
        """
        Compare the differences between the two directories
        :param dir1:
        :param dir2:
        :return:
        """
        if not (dir1 and dir2):
            self.logger.error("Invalid input directory.")
            return False

        cmd_result = self.command.run_cmd("diff -r %s %s" % (dir1, dir2))
        return cmd_result[2] == 0

    def reload_disc(self, device):
        """
        Reloading the media
        :param device:
        :return:
        """
        if not device:
            return False

        self.logger.info("Check to reload the media.")
        self.command.run_cmd("eject %s" % device)
        self.logger.info("Tray ejected.")

        cmd = self.command.run_cmd("eject -t %s" % device)
        if cmd[2] != 0:
            self.logger.error(
                "Could not auto-close the tray, please close the tray manually.")
            self.com_ui.prompt_confirm("Done well?")

        sleep(20)
        self.logger.info("Tray auto-closed.\n")
        return True

    def teardown(self):
        if os.path.exists(self.mnt_dir):
            shutil.rmtree(self.mnt_dir)
        if os.path.exists(self.device_dir):
            shutil.rmtree(self.device_dir)
