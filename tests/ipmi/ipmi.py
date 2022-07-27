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

import argparse

from hwcompatible.test import Test
from hwcompatible.command import Command


class IpmiTest(Test):
    """
    Intelligent Platform Management Interface test
    """
    def __init__(self):
        Test.__init__(self)
        self.requirements = ["OpenIPMI", "ipmitool"]

    def start_ipmi(self):
        """
        Start IPMI test
        :return:
        """
        try:
            self.logger.info("Start ipmp.server.")
            Command("systemctl start ipmi &>> %s" % self.logger.logfile).run()
            Command("systemctl status ipmi.service &>> %s" % self.logger.logfile).get_str(
                regex="Active: active", single_line=False)
        except Exception:
            self.logger.error("Ipmi service start failed")
            return False
        self.logger.info("Ipmi service start successfully")
        return True

    def ipmitool(self):
        """
        Testing with iptool tools
        :return:
        """
        cmd_list = ["ipmitool fru", "ipmitool sensor"]
        for cmd in cmd_list:
            try:
                Command("%s &>> %s " % (cmd, self.logger.logfile)).echo()
            except Exception:
                self.logger.error("%s return error." % cmd)
                return False
            self.logger.info("%s return success." % cmd)
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
