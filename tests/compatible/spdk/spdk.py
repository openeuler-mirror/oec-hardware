#!/usr/bin/env python3
# coding: utf-8

# Copyright (c) 2022 Huawei Technologies Co., Ltd.
# oec-hardware is licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Create: 2022-10-13
# Desc: spdk test

import os

from hwcompatible.test import Test


class SpdkTest(Test):
    def __init__(self):
        Test.__init__(self)
        self.requirements = ["spdk"]
        self.mem_free = 0
        self.hugepage_size = 0
        self.device = None
        self.pci_num = ""
        self.script = "/opt/spdk/scripts/setup.sh"

    def setup(self, args=None):
        """
        Initialization before test
        :param args:
        :return:
        """
        super().setup(args)
        self.device = getattr(args, "device", None)
        self.pci_num = self.device.get_property("DEVPATH").split('/')[-4]

    def test(self):
        """
        Test case
        :return:
        """
        if os.path.exists(self.script):
            ret = self.command.run_cmd(self.script)
            if ret[2] == 0:
                self.logger.info("Load uio_pci_generic driver succeed.")
            else:
                self.logger.error("Load uio_pci_generic driver failed.")
                return False
        else:
            self.logger.error(
                "The spdk version is too low and needs to be upgraded to 21.01.1-5.")
            return False

        # Get MemFree
        self.mem_free = float(self.command.run_cmd("grep MemFree /proc/meminfo | awk '{print $2}'")[0])
        node_count = int(self.command.run_cmd("lscpu | grep 'node(s)'")[0].split(":")[1].strip())
        self.hugepage_size = float(self.command.run_cmd("grep Hugepagesize /proc/meminfo | awk '{print $2}'")[0])

        # Config HugePage
        self.mem_free = self.mem_free / 2
        for node in range(node_count):
            if self.mem_free > self.hugepage_size * 1024:
                self.command.run_cmd(
                    "echo 1024 | tee /sys/devices/system/node/node%s/hugepages/hugepages-2048kB/nr_hugepages" % node)
                self.mem_free = self.mem_free - self.hugepage_size * 1024
                node += 1
            else:
                self.logger.warning("Cancel huge page configuration due to insufficient memory")
                break

        huge_pages_free = self.command.run_cmd("grep HugePages_Free /proc/meminfo")[0].split(":")[1].strip()
        if int(huge_pages_free) > 0:
            self.logger.info("Config hugepage succeed.")
        else:
            self.logger.error("Config hugepage failed.")

        # Start test
        paras = ['read', 'write', 'randread', 'randwrite', 'rw', 'randrw']
        flag = 0
        for para in paras:
            self.logger.info("Start %s test." % para)
            if para in ['rw', 'randrw']:
                rw_flag = 100
                for _ in range(2):
                    ret = self.command.run_cmd(
                        "spdk_nvme_perf -b %s -q 32 -o 3072 -w %s -t 30 -M %s" % (self.pci_num, para, rw_flag))
                    rw_flag = 0
            else:
                ret = self.command.run_cmd("spdk_nvme_perf -b %s -q 32 -o 3072 -w %s -t 30" % (self.pci_num, para))
            if ret[2] != 0:
                flag = 1
                self.logger.error("Test %s failed." % para)
            else:
                self.logger.info("Test %s succeed." % para)

        if flag == 0:
            self.logger.info("Test spdk succeed.")
            return True
        self.logger.error("Test spdk failed.")
        return False

    def teardown(self):
        # Unload uio_pci_generic driver
        if os.path.exists(self.script):
            result = self.command.run_cmd("%s reset" % self.script)
            if result[2] == 0:
                self.logger.info("Unload uio_pci_generic driver succeed.")
                return True
        self.logger.error("Unload uio_pci_generic driver failed.")
        return False
