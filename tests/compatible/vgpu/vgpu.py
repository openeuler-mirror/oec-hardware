#!/usr/bin/env python3
# coding: utf-8
# Copyright (c) 2022 Huawei Technologies Co., Ltd.
# oec-hardware is licensed under the Mulan PSL v2.gica's
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Author: @meitingli
# Create: 2022-06-20
# Desc: VGPU test (current only for x86_64)

import os
import argparse
from hwcompatible.command import Command
from hwcompatible.test import Test

vgpu_dir = os.path.dirname(os.path.realpath(__file__))


class VGpuTest(Test):
    def __init__(self):
        Test.__init__(self)
        self.requirements = ["qemu", "libvirt", "xz", "util-linux", "expect"]
        self.name = ""

    def setup(self, args=None):
        """
        Initialization before test
        """
        self.args = args or argparse.Namespace()
        self.logger = getattr(self.args, "test_logger", None)
        self.name = getattr(self.args, "testname", None)
        self.command = Command(self.logger)

    def test(self):
        """
        Run vgpu test case
        return: result
        """
        result = True
        self.logger.info("Check nvidia server before creating vgpu vm.")
        output = self.command.run_cmd("nvidia-smi")

        self.logger.info("Start to create virtual machine, please wait.")
        self.command.run_cmd("bash %s/test_vgpu.sh create_vm '%s %s'" %
                (vgpu_dir, vgpu_dir, self.name))
        value = self.command.run_cmd("virsh list | grep openEulerVM")
        if value[2] != 0:
            self.logger.error("Create openEuler VM failed.")
            return False
        self.logger.info("Create openEuler VM succeed.")

        self.logger.info("Start to install vgpu driver and test, please wait.")
        testvm = self.command.run_cmd(
            "bash %s/test_vgpu.sh test_vgpu_client" % vgpu_dir)
        if testvm[2] == 0:
            self.logger.info("Test vgpu of openEuler VM succeed.")
        else:
            self.logger.error("Test vgpu of openEuler VM failed.")
            result = False

        self.logger.info("Check nvidia server after creating vgpu vm.")
        output = self.command.run_cmd("nvidia-smi")
        if "vgpu" not in output[0]:
            result = False

        if result:
            self.logger.info("Test vgpu succeed.")
        else:
            self.logger.error("Test vgpu failed.")
        return result

    def teardown(self):
        """
        Clear test env
        """
        destory_cmd = self.command.run_cmd(
            "bash %s/test_vgpu.sh destory_vm %s" % (vgpu_dir, self.name))
        if destory_cmd[2] == 0:
            self.logger.info("Destory openEuler vm succeed.")
        else:
            self.logger.error("Destory openEuler vm failed.")
