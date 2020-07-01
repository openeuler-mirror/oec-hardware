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

import sys
import time

from hwcompatible.test import Test
from hwcompatible.commandUI import CommandUI
from hwcompatible.command import Command
from hwcompatible.device import CertDevice


class UsbTest(Test):
    """
    Usb test
    """
    def __init__(self):
        Test.__init__(self)
        self.requirements = ["usbutils"]
        self.ui = CommandUI()

    def test(self):
        """
        Test case
        :return:
        """
        print("USB device:")
        Command("lsusb -t").echo()
        print("")
        sys.stdout.flush()
        plugged_device = self.get_usb()

        print("USB device plug/unplug test begin...")
        while True:
            print("#############")
            while True:
                print("Please plug in a USB device.")
                if self.ui.prompt_confirm("Done well?"):
                    break
            time.sleep(1)

            new_plugged = self.get_usb()
            if len(new_plugged) <= len(plugged_device):
                print("Error: no USB device add.")
                return False

            new_device = None
            for device in new_plugged:
                if device not in plugged_device:
                    print("Found new USB device.\n")
                    new_device = device
                    break

            if not new_device:
                print("Error: new USB device not found.")
                return False

            print("USB device:")
            Command("lsusb -t").echo()
            print("")
            sys.stdout.flush()
            plugged_device = new_plugged
            while True:
                print("Please unplug the USB device you plugged in just now.")
                if self.ui.prompt_confirm("Done well?"):
                    break
            time.sleep(1)

            new_plugged = self.get_usb()
            if len(new_plugged) >= len(plugged_device):
                print("Error: no USB device unplug.")
                return False

            if new_device in new_plugged:
                print("Error: the USB device can still be found.")
                return False
            else:
                print("USB device unplugged.\n")

            print("USB device:")
            Command("lsusb -t").echo()
            print("#############\n")
            sys.stdout.flush()
            plugged_device = new_plugged

            if self.ui.prompt_confirm("All usb sockets have been tested?"):
                return True

    def get_usb(self):
        """
        Get usb
        :return:
        """
        devices = CertDevice().get_devices()
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
