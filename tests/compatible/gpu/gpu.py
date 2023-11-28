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
# Create: 2022-04-13
# Desc: GPU test, support AMD/NVIDIA series gpu

import argparse
from hwcompatible.command import Command
from hwcompatible.test import Test
from nvidia_gpu import NvidiaGpuTest
from amd_gpu import AMDGpuTest


class GpuTest(Test):
    def __init__(self):
        Test.__init__(self)
        self.requirements = ["gcc-c++", "make", "git"]
        self.device = None

    def setup(self, args=None):
        """
        Initialization before test
        """
        self.args = args or argparse.Namespace()
        self.logger = getattr(args, "test_logger", None)
        self.device = getattr(args, 'device', None)
        self.command = Command(self.logger)
    
    def test(self):
        """
        Test case
        Returns:
            bool: Execution result
        """
        driver = self.device.driver
        if driver == "amdgpu":
            amd_test = AMDGpuTest(self.device, self.logger, self.command)
            result = amd_test.test_amd_gpu()
        else:
            nvidia_test = NvidiaGpuTest(self.device, self.logger, self.command)
            result = nvidia_test.test_nvidia_gpu()
        
        return result
            
        