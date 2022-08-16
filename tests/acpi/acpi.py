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

from hwcompatible.test import Test


class AcpiTest(Test):
    """
    acpi test
    """

    def __init__(self):
        Test.__init__(self)
        self.requirements = ["acpica-tools"]

    def test(self):
        """
        Test case
        :return:
        """
        result = self.command.run_cmd("acpidump")
        if result[2] == 0:
            self.logger.info("Test acpi succeed.")
            return True

        self.logger.error("Test acpi failed.\n%s" % result[1])
        return False
