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

"""clock test"""

import os
import subprocess
from hwcompatible.command import CertCommandError
from hwcompatible.test import Test

clock_dir = os.path.dirname(os.path.realpath(__file__))


class ClockTest(Test):
    """
    Clock Test
    """

    def __init__(self):
        Test.__init__(self)

    def test(self):
        """
        Clock test case
        :return:
        """
        try:
            result = subprocess.getstatusoutput(
                "cd %s; ./clock &>> %s" % (clock_dir, self.logger.logfile))
            if result[0] == 0:
                self.logger.info("Test clock succeed.")
                return True

            self.logger.error("Test clock failed.")
            return False
        except CertCommandError as concrete_error:
            self.logger.error("Test clock failed.\n %s" % concrete_error)
            return False
