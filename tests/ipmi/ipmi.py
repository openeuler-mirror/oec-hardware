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


class IpmiTest(Test):
    """
    Intelligent Platform Management Interface test
    """
    def __init__(self):
        Test.__init__(self)
        self.requirements = ["OpenIPMI", "ipmitool"]

    @staticmethod
    def start_ipmi():
        """
        Start IPMI test
        :return:
        """
        try:
            Command("systemctl start ipmi").run()
            Command("systemctl status ipmi.service").get_str(regex="Active: active", single_line=False)
        except CertCommandError:
            print("ipmi service cant't be started")
            return False
        return True

    @staticmethod
    def ipmitool():
        """
        Testing with iptool tools
        :return:
        """
        cmd_list = ["ipmitool fru", "ipmitool sensor"]
        for cmd in cmd_list:
            try:
                Command(cmd).echo()
            except CertCommandError:
                print("%s return error." % cmd)
                return False
        return True

    def test(self):
        """
        Test case
        :return:
        """
        if not self.start_ipmi():
            return False
        if not self.ipmitool():
            return False
        return True


if __name__ == "__main__":
    i = IpmiTest()
    i.test()
