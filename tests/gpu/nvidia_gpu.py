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
# Create: 2022-10-14
# Desc: Nvidia GPU test

import os
import re
import time
from subprocess import getstatusoutput
gpu_dir = os.path.dirname(os.path.realpath(__file__))


class NvidiaGpuTest():
    def __init__(self, device, logger, command):
        self.device = device
        self.logger = logger
        self.command = command
        self.cuda_samples_log = os.path.join(
            self.logger.logdir, 'cuda_samples.log')
        self.gpu_burn = os.path.join(self.logger.logdir, 'gpu_burn.log')
        self.smi_name = "nvidia-smi"

    def get_driver_info(self):
        """
        Get driver info, includings name, version
        """
        self.logger.info("Vendor Info:", terminal_print=False)
        self.command.run_cmd('lspci -vs %s' % self.device.pci)

        self.logger.info("Driver Info:", terminal_print=False)
        driver = self.device.driver
        if driver == "iluvatar-itr":
            self.smi_name = "ixsmi"
            driver = "bi_driver"
            self.device.set_driver(driver)
        self.logger.info("Driver Name: %s" % driver)

        driver_version = self.device.get_driver_version()
        if driver_version:
            self.logger.info("Driver Version: %s" % driver_version)
        else:
            self.logger.warning(
                "The driver version information cannot be obtained. Please view it manually.")

    def set_default_gpu(self):
        pci = []
        num = []
        pci_key = "GPU 0000" + self.device.get_pci()
        gpu = self.command.run_cmd('%s -q' % self.smi_name, log_print=False)
        for line in gpu[0].split("\n"):
            if "GPU 0000" in line:
                pci.append(line)
            if "Minor Number" in line:
                num.append(line)
        id_num = 0
        output = dict(zip(pci, num))
        if pci_key in output.keys():
            id_num = str(re.findall("\d+", output[pci_key])).strip("['']")
            os.environ['CUDA_VISIBLE_DEVICES'] = id_num

        self.logger.info("Set default test gpu as %s." % id_num)

    def test_pressure(self):
        """
        Set pressure for gpu to test
        Returns:
            bool:
        """
        self.logger.info("Monitor GPU temperature and utilization rate.")
        pci_num = self.device.get_pci()
        self.command.run_cmd(self.smi_name)
        self.command.run_cmd(
            "bash %s/test_nvidia_gpu.sh install_gpu_burn" % gpu_dir)

        os.chdir("/opt/gpu-burn")
        cmd = self.command.run_cmd(
            "nvidia-smi -q | grep -i -A1 '%s' | grep 'Product Name' | cut -d ':' -f 2" % pci_num)
        device_name = cmd[0].strip()
        cmd = self.command.run_cmd(
            "./gpu_burn -l | grep -i '%s' | cut -d ':' -f 1 | awk '{print $2}'" % device_name)
        run_id = cmd[0].strip()
        cmd = getstatusoutput(
            'nohup ./gpu_burn -i%s 10 &> %s &' % (run_id, self.gpu_burn))
        if cmd[0] != 0:
            self.logger.error("Execute gpu_burn failed.")
            return False
        self.logger.info("Execute gpu_burn succeed.")

        time_start = time.time()
        while 1:
            cmd = self.command.run_cmd(
                "ps -ef | grep 'gpu_burn' | grep -v grep", ignore_errors=True)
            if cmd[2] != 0:
                break
            time_delta = time.time() - time_start
            if time_delta >= 500:
                break
            self.command.run_cmd(self.smi_name)
            time.sleep(5)

        return True

    def test_nvidia_gpu(self):
        """
        Nvidia gpu test entry function
        Returns:
            bool:
        """
        result = True
        self.get_driver_info()

        self.logger.info("Check gpu information.")
        self.command.run_cmd('%s -q' % self.smi_name)
        self.logger.info("Check cuda version.")
        self.command.run_cmd('/usr/local/cuda/bin/nvcc --version')

        self.logger.info("Start to test gpu pressure.")
        try:
            if not self.test_pressure():
                result = False

            check_result = self.command.run_cmd(
                "grep 'GPU 0: OK' %s" % self.gpu_burn)
            if os.path.exists(self.gpu_burn) and check_result[2] == 0:
                self.logger.info("Test gpu pressure succeed.")
            else:
                self.logger.error("Test gpu pressure failed.")
                result = False

            self.logger.info("Start to test cuda samples.")
            self.set_default_gpu()
            sample_case = "simpleOccupancy,bandwidthTest,p2pBandwidthLatencyTest,deviceQuery,clock"
            code = self.command.run_cmd(
                "bash %s/test_nvidia_gpu.sh test_cuda_samples '%s %s'" % (gpu_dir, self.cuda_samples_log, sample_case))
            if code[2] == 0:
                self.logger.info("Test cuda samples succeed.")
            else:
                result = False
                self.logger.error("Test cuda samples failed.")
        except Exception as e:
            self.logger.error(
                "Failed to run the script because compiling or setting variables: %s" % e)
            result = False

        return result
