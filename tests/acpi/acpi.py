#!/usr/bin/env python3
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

"""acpi test"""
import subprocess
from hwcompatible.test import Test
from hwcompatible.command import Command


class AcpiTest(Test):
    """
    acpi test
    """

    def __init__(self):
        Test.__init__(self)
        self.requirements = ["acpica-tools"]
        self.logpath = None

    def setup(self, args=None):
        """
        Initialization before test
        :param args:
        :return:
        """
        self.args = args or argparse.Namespace()
        self.logpath = getattr(args, "logdir", None) + "/acpi.log"

    def test(self):
        """
        start test
        """
        try:
            result = subprocess.getstatusoutput(
                "acpidump &> %s" % self.logpath)
            if result[0] == 0:
                print("Test acpi succeed.")
                return True

            print("Test acpi failed.")
            return False
        except Exception as concrete_error:
            print("Test acpi failed.\n %s" % concrete_error)
            return False
