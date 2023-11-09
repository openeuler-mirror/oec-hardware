#!/usr/bin/env python3
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
# Create: 2020-04-01

import re
from subprocess import getoutput


class SysInfo:
    """
    Deal system information
    """

    def __init__(self, filename):
        self.product = None
        self.version = None
        self.kernel = None
        self.arch = None
        self.kernel_rpm = None
        self.kerneldevel_rpm = None
        self.kernel_version = None
        self.debug_kernel = False
        self._load(filename)

    def get_product(self):
        """
         Get product information
        :return:
        """
        return self.product

    def get_version(self):
        """
         Get system version information
        :return:
        """
        return self.version

    def get_kernel(self):
        """
         Get kernel information
        :return:
        """
        return self.kernel

    def _load(self, filename):
        """
        Collect system information
        :param filename:
        :return:
        """
        text = ""
        with open(filename) as file_content:
            text = file_content.read()

        if text:
            pattern = re.compile(r'NAME="(.+)"')
            results = pattern.findall(text)
            self.product = results[0].strip() if results else ""

            pattern = re.compile(r'VERSION="(.+)"')
            results = pattern.findall(text)
            self.version = results[0].strip() if results else ""

        self.arch = getoutput('uname -m')
        self.debug_kernel = "debug" in self.arch
        self.kernel = getoutput('uname -r')
        self.kernel_rpm = "kernel-{}".format(self.kernel)
        self.kerneldevel_rpm = "kernel-devel-{}".format(self.kernel)
        self.kernel_version = self.kernel.split('-')[0]
