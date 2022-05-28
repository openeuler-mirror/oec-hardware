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
# Create: 2022-04-13

"""gpu test"""
import os
import subprocess
import argparse
import time
import shutil
import re

from hwcompatible.command import Command, CertCommandError
from hwcompatible.test import Test

gpu_dir = os.path.dirname(os.path.realpath(__file__))


class GpuTest(Test):
    """
        gpu test
    """

    def __init__(self):
        Test.__init__(self)
        self.args = None
        self.device = None
        self.requirements = ["gcc-c++", "make", "tar", "git"]

    def setup(self, args=None):
        self.args = args or argparse.Namespace()
        self.name = getattr(args, 'testname', None)
        self.device = getattr(args, 'device', None)
        self.logpath = getattr(args, "logdir", None) + "/" + self.name + ".log"
        self.cuda_samples_log = getattr(
            args, 'logdir', None) + '/cuda_samples.log'
        self.gpu_burn = getattr(args, 'logdir', None) + '/gpu_burn.log'

    def current_card(self):
        print("Vendor Info:")
        pci_num = self.device.get_property("DEVPATH").split('/')[-1]
        Command('lspci -s %s -v' % pci_num).echo()

        print("Driver Info:")
        driver = self.device.get_property("DRIVER")
        Command('modinfo %s | head -n 13' % driver).echo()
        return pci_num

    def pressure(self):
        print("Monitor GPU temperature and utilization rate.")
        pci = []
        num = []
        pci_key = "GPU 0000" + self.current_card()
        gpu = Command('nvidia-smi -q')
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
            os.system('nvidia-smi &>>%s' % self.logpath)
            time.sleep(1)

    def test(self):
        try:
            result = True
            print("Start to test gpu pressure.")
            self.pressure()
            if os.path.exists(self.gpu_burn) and os.system("grep 'GPU 0: OK' %s" % self.gpu_burn) == 0:
                print("Test gpu pressure succeed.")
            else:
                print("Test gpu pressure failed.")
                result = False

            print("Start to test cuda samples.")
            sample_case = "simpleOccupancy,bandwidthTest,p2pBandwidthLatencyTest,deviceQuery,clock"
            code = os.system(
                "bash %s/test_gpu.sh test_cuda_samples '%s %s'" % (gpu_dir, self.cuda_samples_log, sample_case))
            if code == 0:
                print("Test cuda samples succeed.")
            else:
                result = False
                print("Test cuda samples failded.")

            return result
        except Exception as e:
            print("Failed to run the script because compiling or setting variables", e)
            return False

    def teardown(self):
        os.system("rm -rf /opt/gpu-burn /opt/cuda-samples-master")
