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
# Author: @meitingli
# Create: 2022-10-15
# Desc: AMD GPU test (This test could only execute on graphical.target)

import os
from subprocess import getstatusoutput

gpu_dir = os.path.dirname(os.path.realpath(__file__))


class AMDGpuTest():
    def __init__(self, device, logger, command):
        self.device = device
        self.logger = logger
        self.command = command
        self.radeontop_log = os.path.join(self.logger.logdir, 'radeontop.log')
        self.screen_info_log = os.path.join(
            self.logger.logdir, 'screen_info.log')
        self.glmark_log = os.path.join(self.logger.logdir, 'glmark2.log')

    def get_driver_info(self):
        """
        Get driver info, includings name, version
        """
        self.logger.info("Vendor Info:", terminal_print=False)
        self.command.run_cmd('lspci -vs %s' % self.device.pci)

        self.logger.info("Driver Info:", terminal_print=False)
        driver = self.device.driver
        self.logger.info("Driver Name: %s" % driver)

        driver_version = self.device.get_driver_version()
        if driver_version:
            self.logger.info("Driver Version: %s" % driver_version)
        else:
            self.logger.warning(
                "The driver version information cannot be obtained. Please view it manually.")

    def test_pressure(self):
        """
        Set pressure for gpu to test
        This test need graphical.target to support
        Returns:
            bool:
        """
        os.chdir("/opt/glmark2/build/src")
        cmd = getstatusoutput(
            './glmark2 --off-screen | tee %s' % self.glmark_log)
        if cmd[0] != 0:
            self.logger.error("Test gpu pressure failed.")
            return False
        self.logger.info("Test gpu pressure succeed.")

        cmd = self.command.run_cmd(
            "grep 'glmark2 Score' %s" % self.glmark_log)
        if cmd[2] == 0:
            self.logger.info("Check gpu glmark2 score succeed.")
        else:
            self.logger.error("Check gpu glmark2 score failed.")
            return False

        return True

    def test_screen_info(self):
        """
        Test screen information for gpu
        This test need graphical.target to support
        Returns:
            bool:
        """
        os.chdir("/opt/glmark2/build/src")
        cmd = self.command.run_cmd(
            "./glmark2 -l | tee %s " % self.screen_info_log)
        if cmd[2] == 0:
            self.logger.info("Test gpu screen information succeed.")
        else:
            self.logger.error("Test gpu screen information failed.")
            return False

        return True

    def test_radeontop(self):
        """
        Check gpu utilization by radeontop, it can execute multi times and has log file
        Returns:
            bool:
        """
        os.chdir("/opt/radeontop")
        cmd = getstatusoutput(
            "echo q | ./radeontop | tee %s" % self.radeontop_log)
        if cmd[0] == 0:
            self.logger.info("Check gpu radeontop succeed.")
        else:
            self.logger.error("Check gpu radeontop failed.")
            return False

        return True

    def test_amd_gpu(self):
        """
        AMD gpu test entry function
        Returns:
            bool:
        """
        result = True
        self.get_driver_info()
        self.command.run_cmd(
            "bash %s/test_amd_gpu.sh install_readontop" % gpu_dir)
        self.command.run_cmd(
            "bash %s/test_amd_gpu.sh install_glmark2" % gpu_dir)
        
        self.logger.info("Check gpu radeontop.")
        try:
            if not self.test_radeontop():
                result = False

            if not self.test_screen_info():
                result = False

            self.logger.info("Start to test gpu pressure.")
            if not self.test_pressure():
                result = False
            self.logger.info("End to test gpu pressure.")

        except Exception as e:
            self.logger.error(
                "Failed to run the script because compiling or setting variables: %s" % e)
            result = False

        return result
