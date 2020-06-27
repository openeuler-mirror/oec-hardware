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

from hwcompatible.test import Test
from hwcompatible.command import Command, CertCommandError


class AcpiTest(Test):
    """
    acpi test
    """
    def __init__(self):
        Test.__init__(self)
        self.requirements = ["acpica-tools"]

    @staticmethod
    def test():
        try:
            Command("acpidump").echo()
            return True
        except CertCommandError as e:
            print(e)
            return False