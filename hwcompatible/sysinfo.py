#!/usr/bin/env python
# coding: utf-8

# Copyright (c) 2020 Huawei Technologies Co., Ltd.
# oec-hardware is licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Create: 2020-04-01

import os
import re


class SysInfo:
    """
    Get system information
    """
    def __init__(self, filename):
        self.product = None
        self.version = None
        self.update = None
        self.valid = False
        self.kernel = None
        self.arch = None
        self.kernel_rpm = None
        self.kerneldevel_rpm = None
        self.kernel_version = None
        self.debug_kernel = False
        self.load(filename)

    def load(self, filename):
        """
        Collect system information
        :param filename:
        :return:
        """
        try:
            f = open(filename)
            text = f.read()
            f.close()
        except:
            print("Release file not found.")
            return

        if text:
            pattern = re.compile(r'NAME="(\w+)"')
            results = pattern.findall(text)
            self.product = results[0].strip() if results else ""

            pattern = re.compile(r'VERSION="(.+)"')
            results = pattern.findall(text)
            self.version = results[0].strip() if results else ""

        with os.popen('uname -m') as p:
            self.arch = p.readline().strip()
            self.debug_kernel = "debug" in self.arch

        with os.popen('uname -r') as p:
            self.kernel = p.readline().strip()
            self.kernel_rpm = "kernel-{}".format(self.kernel)
            self.kerneldevel_rpm = "kernel-devel-{}".format(self.kernel)
            self.kernel_version = self.kernel.split('-')[0]

    def get_version(self):
        """
         Get system version information
        :return:
        """
        return self.version
