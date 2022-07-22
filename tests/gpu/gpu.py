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
# Create: 2022-04-13

import os
import subprocess
import argparse
import time
import re

from hwcompatible.command import Command
from hwcompatible.test import Test

gpu_dir = os.path.dirname(os.path.realpath(__file__))


class GpuTest(Test):
    """
    Gpu test
    """

    def __init__(self):
        Test.__init__(self)
        self.device = None
        self.gpu_burn = ""
        self.cuda_samples_log = ""
        self.requirements = ["gcc-c++", "make", "tar", "git"]

    def setup(self, args=None):
        self.args = args or argparse.Namespace()
        self.logger = getattr(args, "test_logger", None)
        self.device = getattr(args, 'device', None)
        self.log_path = self.logger.logfile
        self.cuda_samples_log = getattr(
            args, 'logdir', None) + '/cuda_samples.log'
        self.gpu_burn = getattr(args, 'logdir', None) + '/gpu_burn.log'
        self.smi_name = "nvidia-smi"

    def current_card(self):
        self.logger.info("Vendor Info:")
        pci_num = self.device.get_property("DEVPATH").split('/')[-1].upper()
        Command('lspci -s %s -v &>> %s' % (pci_num, self.log_path)).echo()

        self.logger.info("Driver Info:")
        driver = self.device.get_property("DRIVER")
        if driver == "iluvatar-itr":
            self.smi_name = "ixsmi"
            driver = "bi_driver"
            self.device.set_driver(driver)
        Command('modinfo %s | head -n 13 &>> %s' % (driver, self.log_path)).echo()
        self.logger.info("Driver Name:")
        driver_version = self.device.get_driver_version()
        if not driver_version:
            self.logger.warning("The driver version information cannot be obtained. Please view it manually.")
        else:
            self.logger.info("Driver Version: %s" % driver_version)
        return pci_num

    def pressure(self):
        self.logger.info("Monitor GPU temperature and utilization rate.")
        pci = []
        num = []
        pci_key = "GPU 0000" + self.current_card()
        gpu = Command('%s -q' % self.smi_name)
        gpu.run_quiet()
        for line in gpu.output:
            if "GPU 0000" in line:
                pci.append(line)
            if "Minor Number" in line:
                num.append(line)

        output = dict(zip(pci, num))
        if pci_key in output.keys():
            id_num = str(re.findall("\d+", output[pci_key])).strip("['']")
            os.environ['CUDA_VISIBLE_DEVICES'] = id_num

        os.system("bash %s/test_gpu.sh install_gpu_burn" % gpu_dir)
        os.system('cd /opt/gpu-burn && nohup ./gpu_burn 10 &> %s &' %
                  self.gpu_burn)
        time.sleep(1)
        while not subprocess.call("ps -ef | grep 'gpu_burn' | grep -v grep >/dev/null", shell=True):
            Command('%s &>> %s' % (self.smi_name, self.log_path)).run()
            time.sleep(1)

    def test(self):
        try:
            result = True
            self.logger.info("Start to test gpu pressure.")
            self.pressure()
            if os.path.exists(self.gpu_burn) and os.system("grep 'GPU 0: OK' %s" % self.gpu_burn) == 0:
                self.logger.info("Test gpu pressure succeed.")
            else:
                self.logger.error("Test gpu pressure failed.")
                result = False

            self.logger.info("Start to test cuda samples.")
            sample_case = "simpleOccupancy,bandwidthTest,p2pBandwidthLatencyTest,deviceQuery,clock"
            code = os.system(
                "bash %s/test_gpu.sh test_cuda_samples '%s %s'" % (gpu_dir, self.cuda_samples_log, sample_case))
            if code == 0:
                self.logger.info("Test cuda samples succeed.")
            else:
                result = False
                self.logger.error("Test cuda samples failded.")

            return result
        except Exception as e:
            self.logger.error("Failed to run the script because compiling or setting variables %s" % e)
            return False
