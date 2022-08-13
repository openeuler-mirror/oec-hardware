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
# Desc: Intelligent Platform Management Interface test

from hwcompatible.test import Test


class IpmiTest(Test):
    def __init__(self):
        Test.__init__(self)
        self.requirements = ["OpenIPMI", "ipmitool"]

    def start_ipmi(self):
        """
        Start IPMI test
        :return:
        """
        self.command.run_cmd("systemctl start ipmi")
        result = self.command.run_cmd("systemctl status ipmi.service | grep 'Active: active'" )
        if result[2] != 0:
            self.logger.error("Ipmi service start failed.")
            return False
        self.logger.info("Ipmi service start succeed.")
        return True

    def ipmitool(self):
        """
        Testing with iptool tools
        :return:
        """
        cmd_list = ["ipmitool fru", "ipmitool sensor"]
        for cmd in cmd_list:
            result = self.command.run_cmd(cmd)
            if result[2] != 0:
                self.logger.error("%s execute failed." % cmd)
                return False
            self.logger.info("%s execute successfully." % cmd)
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
