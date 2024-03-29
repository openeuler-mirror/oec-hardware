#!/usr/bin/env python3
# coding: utf-8
# Copyright (c) 2022 Huawei Technologies Co., Ltd.
# oec-hardware is licensed under the Mulan PSL v2.gica's
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Author: @meitingli
# Create: 2022-03-28
# Desc: Public key card test

import argparse
from sds_keycard import SDSKeyCardTest
from tsse_keycard import TSSEKeyCardTest
from hwcompatible.test import Test


class KeyCardTest(Test):
    def __init__(self):
        Test.__init__(self)
        self.device = None
        self.keycard_test = None

    def setup(self, args=None):
        """
        Initialization before test
        """
        self.args = args or argparse.Namespace()
        self.device = getattr(args, 'device', None)
        if self.device.driver == "tsse":
            self.keycard_test = TSSEKeyCardTest()
        else:
            self.keycard_test = SDSKeyCardTest()
        self.keycard_test.setup(args)

    def test(self):
        """
        Run key card test case
        return: result
        """
        return self.keycard_test.test()

    def teardown(self):
        """
        Environment recovery after test
        :return:
        """
        self.keycard_test.teardown()