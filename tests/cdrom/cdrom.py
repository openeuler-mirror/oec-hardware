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

"""cdrom test"""

import os
import sys
import time
import shutil
import argparse

from hwcompatible.test import Test
from hwcompatible.command_ui import CommandUI
from hwcompatible.command import Command, CertCommandError


class CDRomTest(Test):
    """
    CDRom Test
    """
    def __init__(self):
        Test.__init__(self)
        self.requirements = ["dvd+rw-tools", "genisoimage", "wodim", "util-linux"]
        self.method = None
        self.device = None
        self.type = None
        self.args = None
        self.com_ui = CommandUI()
        self.test_dir = "/usr/share/doc"

    def setup(self, args=None):
        """
        The Setup before testing
        :param args:
        :return:
        """
        self.args = args or argparse.Namespace()
        self.logger = getattr(args, "test_logger", None)
        self.log_path = self.logger.logfile
        self.device = getattr(args, "device", None)
        self.type = self.get_type(self.device)
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
        Command("eject %s &>> %s" % (devname, self.log_path)).run(ignore_errors=True)
        while True:
            self.logger.info("Please insert %s disc into %s, then close the tray manually."
                             % (self.type.lower(), devname))
            if self.method == "write_test":
                self.logger.info("Tips:disc should be new.")
            elif self.method == "read_test":
                self.logger.info("Tips:disc should not be blank.")
            if self.com_ui.prompt_confirm("Done well?"):
                break
        Command("eject -t %s &>> %s" % (devname, self.log_path)).run(ignore_errors=True)
        self.logger.warning("Waiting media...")
        time.sleep(20)

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

        self.logger.error("Can not find proper test-type for %s." % device.get_name())
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
        try:
            devname = self.device.get_property("DEVNAME")
            Command("umount %s" % devname).run(ignore_errors=True)
            if "BD" in self.type:
                self.logger.info("Formatting ...")
                sys.stdout.flush()
                Command("dvd+rw-format -format=full %s 2>/dev/null" % devname).echo()
                self.reload_disc(devname)
                sys.stdout.flush()
                return self.write_test()
            elif "DVD_PLUS" in self.type:
                self.logger.info("Formatting ...")
                sys.stdout.flush()
                Command("dvd+rw-format -force %s 2>/dev/null" % devname).echo()
                self.reload_disc(devname)
                sys.stdout.flush()
                return self.write_test()
            else:
                self.logger.info("Blanking ...")
                sys.stdout.flush()
                # blankCommand = Command("cdrecord -v dev=%s blank=fast" % devname).echo()
                Command("cdrecord -v dev=%s blank=fast &>> %s" % (devname, self.log_path)).echo()
                self.reload_disc(devname)
                sys.stdout.flush()
                return self.write_test()
        except CertCommandError:
            return False

    def write_test(self):
        """
        Write mode test of CDROM
        :return:
        """
        try:
            devname = self.device.get_property("DEVNAME")
            Command("umount %s" % devname).run(ignore_errors=True)
            if "BD" in self.type or "DVD_PLUS" in self.type:
                Command("growisofs -Z %s -quiet -R %s &>> %s" % (devname, self.test_dir, self.log_path)).echo()
                self.reload_disc(devname)
                sys.stdout.flush()
                return True
            else:
                write_opts = "-sao"
                try:
                    command = Command("cdrecord dev=%s -checkdrive" % devname)
                    modes = command.get_str(regex="^Supported modes[^:]*:(?P<modes>.*$)", \
                                            regex_group="modes",
                                            single_line=False, ignore_errors=True)
                    if "TAO" in modes:
                        write_opts = "-tao"
                    if "SAO" in modes:
                        write_opts = "-sao"
                    flags = command.get_str(regex="^Driver flags[^:]*:(?P<flags>.*$)", \
                                            regex_group="flags",
                                            single_line=False, ignore_errors=True)
                    if "BURNFREE" in flags:
                        write_opts += " driveropts=burnfree"
                except CertCommandError as concrete_error:
                    self.logger.error(concrete_error)

                size = Command("mkisofs -quiet -R -print-size %s " % self.test_dir).get_str()
                blocks = int(size)

                Command("mkisofs -quiet -R %s | cdrecord -v %s dev=%s fs=32M tsize=%ss - &>> %s" %
                        (self.test_dir, write_opts, devname, blocks, self.log_path)).echo()
                self.reload_disc(devname)
                sys.stdout.flush()
                return True
        except CertCommandError as concrete_error:
            return False

    def read_test(self):
        """
        Read mode test of CDROM
        :return:
        """
        try:
            devname = self.device.get_property("DEVNAME")
            if os.path.exists("mnt_cdrom"):
                shutil.rmtree("mnt_cdrom")
            os.mkdir("mnt_cdrom")

            self.logger.info("Mounting media ...")
            Command("umount %s" % devname).echo(ignore_errors=True)
            Command("mount -o ro %s ./mnt_cdrom" % devname).echo()

            size = Command("df %s | tail -n1 | awk '{print $3}' &>> %s" %
                           (devname, self.log_path)).get_str()
            size = int(size)
            if size == 0:
                self.logger.error("Blank disc.")
                Command("umount ./mnt_cdrom &>> %s" % self.log_path).run(ignore_errors=True)
                shutil.rmtree("mnt_cdrom")
                return False

            if os.path.exists("device_dir"):
                shutil.rmtree("device_dir")
            os.mkdir("device_dir")

            self.logger.info("Copying files ...")
            sys.stdout.flush()
            Command("cp -dpRf ./mnt_cdrom/. ./device_dir/ &>> %s", self.log_path).run()

            self.logger.info("Comparing files ...")
            sys.stdout.flush()
            return_code = self.cmp_tree("mnt_cdrom", "device_dir")
            Command("umount ./mnt_cdrom").run(ignore_errors=True)
            shutil.rmtree("./mnt_cdrom")
            shutil.rmtree("./device_dir")
            return return_code
        except CertCommandError as concrete_error:
            print(concrete_error)
            return False

    def cmp_tree(self, dir1, dir2):
        """
        Compare the differences between the two directories
        :param dir1:
        :param dir2:
        :return:
        """
        if not (dir1 and dir2):
            self.logger.info("Error: invalid input dir.")
            return False
        try:
            Command("diff -r %s %s &>> %s" % (dir1, dir2, self.log_path)).run()
            return True
        except CertCommandError:
            self.logger.error("File comparison failed.")
            return False

    def reload_disc(self, device):
        """
        Reloading the media
        :param device:
        :return:
        """
        if not device:
            return False

        self.logger.info("Reloading the media ... ")
        sys.stdout.flush()
        try:
            Command("eject %s &>> %s" % (device, self.log_path)).run()
            self.logger.info("tray ejected.")
            sys.stdout.flush()
        except Exception:
            pass

        try:
            Command("eject -t %s &>> %s" % (device, self.log_path)).run()
            self.logger.info("tray auto-closed.\n")
            sys.stdout.flush()
        except Exception:
            self.logger.error("Could not auto-close the tray, please close the tray manually.")
            self.com_ui.prompt_confirm("Done well?")

        time.sleep(20)
        return True
