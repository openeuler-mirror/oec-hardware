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
# Desc: Usb test

import time
from hwcompatible.test import Test
from hwcompatible.command_ui import CommandUI
from hwcompatible.device import CertDevice


class UsbTest(Test):
    def __init__(self):
        Test.__init__(self)
        self.requirements = ["usbutils"]
        self.com_ui = CommandUI()

    def test(self):
        """
        Test case
        :return:
        """
        self.logger.info("USB device:")
        self.command.run_cmd("lsusb -t")
        plugged_device = self.get_usb()

        self.logger.info("USB device plug/unplug test begin...")
        while True:
            while True:
                self.logger.info("Please plug in a USB device.")
                if self.com_ui.prompt_confirm("Done well?"):
                    break
            time.sleep(1)

            new_plugged = self.get_usb()
            if len(new_plugged) <= len(plugged_device):
                self.logger.error("No USB device add.")
                return False

            new_device = None
            for device in new_plugged:
                if device not in plugged_device:
                    self.logger.info("Found new USB device.")
                    new_device = device
                    break

            if not new_device:
                self.logger.error("New USB device not found.")
                return False

            self.logger.info("USB device:")
            self.command.run_cmd("lsusb -t")

            plugged_device = new_plugged
            while True:
                self.logger.info("Please unplug the USB device you plugged in just now.")
                if self.com_ui.prompt_confirm("Done well?"):
                    break
            time.sleep(1)

            new_plugged = self.get_usb()
            if len(new_plugged) >= len(plugged_device):
                self.logger.error("No USB device unplug.")
                return False

            if new_device in new_plugged:
                self.logger.error("The USB device can still be found.")
                return False
            else:
                self.logger.info("USB device unplugged.")

            self.logger.info("USB device:")
            self.command.run_cmd("lsusb -t")
            plugged_device = new_plugged

            if self.com_ui.prompt_confirm("All usb sockets have been tested?"):
                return True

    def get_usb(self):
        """
        Get usb
        :return:
        """
        devices = CertDevice(self.logger).get_devices()
        usb_devices = list()
        for device in devices:
            if (device.get_property("SUBSYSTEM") != "usb" or
                device.get_property("DEVTYPE") != "usb_device" or
                device.get_property("ID_BUS") != "usb" or
                device.get_property("BUSNUM") == "" or
                    device.get_property("DEVNUM") == ""):
                continue
            else:
                usb_devices.append(device.path)
        return usb_devices
