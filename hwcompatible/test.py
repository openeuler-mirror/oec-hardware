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
# Desc: Test template

import argparse
from hwcompatible.command import Command


class Test:
    """
    Test template
    """

    def __init__(self):
        """
        Initialize the Test instance with default attributes.
        """
        self.pri = 0  # Priority level of the test
        self.requirements = list()  # List of requirements needed for the test
        self.reboot = False  # Indicates whether a reboot is required after the test
        self.rebootup = None  # Action to take after rebooting
        self.args = None  # Command-line arguments
        self.logger = None  # Logger instance for logging messages
        self.command = None  # Command object for executing shell commands
        self.log_path = ""  # Path to the log file

    def setup(self, args=None):
        """
        setup
        """
        self.args = args or argparse.Namespace()
        self.logger = getattr(self.args, "test_logger", None)
        self.command = Command(self.logger)

    def show_driver_info(self):
        """
        show driver name and driver version
        """
        driver_name = self.device.get_driver()
        driver_version = self.device.get_driver_version()
        self.logger.info("Driver Name: %s" % driver_name)
        if not driver_version:
            self.logger.info(
                "The driver version information cannot be obtained. Please view it manually.")
        else:
            self.logger.info("Driver Version: %s" % driver_version)

    def teardown(self):
        """
        teardown
        """
        pass
