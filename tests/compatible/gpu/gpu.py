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
from typing import TYPE_CHECKING, Optional
from hwcompatible.command import Command
from hwcompatible.device import Device
from hwcompatible.test import Test
from nvidia_gpu import NvidiaGpuTest
from amd_gpu import AMDGpuTest
from metax_gpu import MetaXGpuTest

if TYPE_CHECKING:
    from hwcompatible.log import Logger


class GpuTest(Test):
    def __init__(self):
        Test.__init__(self)
        self.requirements = ["gcc-c++", "make", "git"]
        self.device: Optional[Device] = None

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
        if self.logger is None:
            return False
        if self.device is None:
            self.logger.error("No GPU device found.")
            return False
        if self.command is None:
            self.logger.error("Command helper is not initialized.")
            return False

        logger: "Logger" = self.logger
        command = self.command
        driver = self.device.driver
        if driver == "amdgpu":
            amd_test = AMDGpuTest(self.device, logger, command)
            result = amd_test.test_amd_gpu()
        elif driver == "METAX":
            metax_test = MetaXGpuTest(self.device, logger, command)
            result = metax_test.test_metax_gpu()
        else:
            nvidia_test = NvidiaGpuTest(self.device, logger, command)
            result = nvidia_test.test_nvidia_gpu()
        
        return result
            
        
