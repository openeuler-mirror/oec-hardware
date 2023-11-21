#!/usr/bin/env python3
# coding: utf-8
# Copyright (c) 2023 Huawei Technologies Co., Ltd.
# oec-hardware is licensed under the Mulan PSL v2.gica's
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Author: @liqiang1118
# Create: 2023-05-15
# Desc: Public kabi test

import os
import shutil
import argparse
from subprocess import getoutput
from hwcompatible.command import Command
from hwcompatible.test import Test

kabi_whitelist_dir = os.path.dirname(os.path.realpath(__file__))


class KabiWhiteListTest(Test):
    def __init__(self):
        Test.__init__(self)
        self.requirements = ["gzip", "rpm-build"]

    def setup(self, args=None):
        """
        Initialization before test
        """
        self.args = args or argparse.Namespace()
        self.logger = getattr(self.args, "test_logger", None)
        self.command = Command(self.logger)

    def test(self):
        """
        Run kabi test case
        return: result
        """
        self.command.run_cmd("bash %s/kabi_check.sh" % kabi_whitelist_dir)
        ko_result = self.command.run_cmd("ls %s/test_log/ | grep noko" % kabi_whitelist_dir)
        if ko_result[2] == 0:
            self.logger.error("Please configure the board information in the configuration file")
            return False
        self.logger.info("Ko or rpm check complete")

        test_result = self.command.run_cmd("ls %s/test_log | grep change" % kabi_whitelist_dir)
        if test_result[2] == 0:
            self.logger.error("Kabiwhitelist test fail")
            return False
        return True

    def teardown(self):
        """
        Clear temporary files
        """
        file_name = "/usr/share/oech/lib/tests/kabiwhitelist/test_log"
        if os.path.exists(file_name):
            shutil.rmtree(file_name)
        self.logger.info("Clearing temporary files is complete")
