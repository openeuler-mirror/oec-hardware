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
# Desc: vgpu test (current only for x86_64)

import os
import argparse
from subprocess import getstatusoutput
from hwcompatible.command import Command
from hwcompatible.test import Test

vgpu_dir = os.path.dirname(os.path.realpath(__file__))


class VGpuTest(Test):
    """
    VGpu Test
    """

    def __init__(self):
        Test.__init__(self)
        self.requirements = ["qemu", "libvirt", "xz", "util-linux", "expect"]
        self.logfile = None
        self.name = ""

    def setup(self, args=None):
        """
        Initialization before test
        """
        self.args = args or argparse.Namespace()
        self.logger = getattr(self.args, "test_logger", None)
        self.logfile = self.logger.logfile
        self.name = getattr(self.args, "testname", None)

    def test(self):
        """
        Run vgpu test case
        return: result
        """
        result = True
        output = Command("nvidia-smi").read()
        self.logger.info(
            "Check nvidia server before creating vgpu vm: %s" % output, terminal_print=False)

        self.logger.info("Start to create virtual machine, please wait.")
        Command("bash %s/test_vgpu.sh create_vm '%s %s'" %
                (vgpu_dir, vgpu_dir, self.name)).run()
        value = getstatusoutput("virsh list | grep openEulerVM")
        if value[0] != 0:
            self.logger.error("Create openEuler VM failed.")
            return False
        self.logger.info("Create openEuler VM succeed.\n %s" % value[1])

        self.logger.info("Start to install vgpu driver and test, please wait.")
        testvm = Command(
            "bash %s/test_vgpu.sh test_vgpu_client &>>%s" % (vgpu_dir, self.logfile))
        testvm.run()
        if testvm.returncode == 0:
            self.logger.info("Test vgpu of openEuler VM succeed.")
        else:
            self.logger.error("Test vgpu of openEuler VM failed.")
            result = False

        output = Command("nvidia-smi").read()
        self.logger.info(
            "Check nvidia server after creating vgpu vm: %s" % output, terminal_print=False)
        if "vgpu" not in output:
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
        destory_cmd = Command(
            "bash %s/test_vgpu.sh destory_vm %s" % (vgpu_dir, self.name))
        destory_cmd.run()
        if destory_cmd.returncode == 0:
            self.logger.info("Destory openEuler vm succeed.")
        else:
            self.logger.error("Destory openEuler vm failed.")
