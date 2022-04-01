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

class GpuTest(Test):
    """
        gpu test
    """
    def __init__(self):
        Test.__init__(self)
        self.args = None
        self.device = None
        self.requirements = ["gcc-c++"]
        

    def setup(self, args=None):
        self.args = args or argparse.Namespace()
        self.device = getattr(args, 'device', None)
        self.nohup = getattr(args, 'logdir', None)+'/nohup.out'
    
    def current_card(self):
        print("Vendor Info:")
        pci_num = self.device.get_property("DEVPATH").split('/')[-1]
        Command('lspci -s %s -v' % pci_num).echo()
        
        print("Drive Info:")
        driver = self.device.get_property("DRIVER")
        Command('modinfo %s|head -n 13' % driver).echo()
        return pci_num

    def pressure(self):
        print("Monitor GPU temperature and utilization rate")
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
        
        output= dict(zip(pci,num))
        if pci_key in output.keys():
            id_num = str(re.findall("\d+", output[pci_key])).strip("['']")
        os.environ['CUDA_VISIBLE_DEVICES'] = id_num
        
        os.system('nohup gpu_burn 10 &> %s &' % self.nohup)
        # Pressure measurement
        time.sleep(1)
        while not subprocess.call("ps -ef |grep 'gpu_burn' | grep -v grep", shell=True):
            Command('nvidia-smi').echo()
            time.sleep(1)
        
    def samples(self):
        print('Run test case')
        files = Command("find / -wholename '*/cuda-samples/bin/*/linux/release'")
        files.run_quiet()
        filepath = files.output
        if filepath:
            path = ''.join(filepath)
            os.chdir(path)
        else:
            return False

        sample_list = ['simpleOccupancy', 'bandwidthTest', 'p2pBandwidthLatencyTest', \
                'deviceQuery', 'clock']
        result = True
        for sample in sample_list:
            print('INFO: ==================     %s     ===============' % sample)
            try:
                m = Command('./%s' % sample)
                m.echo()
                print(' %s is pass\n' % sample)
            except Exception as ex: 
                print(' %s is failed\n' % sample)
                result = False
        if not result:
            return False
        else:
            return True

    def test(self):
        try:
            self.pressure()
            # Check whether the pressure test is successful
            if os.path.exists(self.nohup) and subprocess.call \
                    ("ps -ef |grep 'gpu_burn' | grep -v grep", shell=True) != 0:
                        with open(self.nohup) as f:
                            for content in f.readlines():
                                line = content.strip()
                                if "FAULTY" in line or "Error" in line:
                                    print("Pressure test failed\n")
                                    return False 
    
            if not self.samples():
                return False
            return True
        except Exception as e:
            print("Failed to run the script because compiling or setting variables", e)
            return False
