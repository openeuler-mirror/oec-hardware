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
# Desc: Fibre channel test

import argparse
from hwcompatible.test import Test
from hwcompatible.command import Command
from tests.compatible.disk.common import query_disk, get_disk, raw_test, vfs_test, valid_disk


class FCTest(Test):
    def __init__(self):
        Test.__init__(self)
        self.disks = list()
        self.requirements = ["fio"]
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
        self.logger = getattr(self.args, "test_logger", None)
        self.command = Command(self.logger)
        self.config_data = getattr(self.args, "config_data", None)

        self.device = getattr(self.args, 'device', None)
        self.pci_num = self.device.get_property("DEVPATH").split('/')[-1]
        self.show_driver_info()
        self.logger.info("Vendor Info:", terminal_print=False)
        self.command.run_cmd("lspci -s %s -v" % self.pci_num)
        query_disk(self.logger, self.command)

    def test(self):
        """
        Start test
        """
        pci_num = self.check_link_state()
        if not pci_num:
            return False
        self.disks = get_disk(self.logger, self.command, self.config_data, pci_num)
        if len(self.disks) == 0:
            self.logger.error("No suite disk found to test.")
            return False

        if not self.config_data:
            self.logger.error("Failed to get disk from configuration file.")
            return False

        disk = self.config_data.get('disk', '')
        if not valid_disk(self.logger, disk, self.disks):
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
    
    def check_link_state(self):
        """
        check HBA link state
        """
        host_name = self.command.run_cmd("ls -l /sys/class/fc_host | grep %s | awk '{print $9}'"
                % self.pci_num)[0].strip('\n')
        port_state = self.command.run_cmd("cat /sys/class/fc_host/%s/port_state" % host_name)[0].strip('\n')
        if port_state == "Linkdown":
            self.logger.error("The HBA's port_state is linkdown, Please check the connection state!")
            return ""
        elif port_state == "Online":
            pci_num = self.pci_num
            self.logger.info("The HBA's port_state is Online, start testing...")
            return pci_num
        else:
            self.logger.info("The HBA's port_state can't be viewed")
            return False

