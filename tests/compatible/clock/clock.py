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
# Desc: Clock test

import os
from hwcompatible.test import Test

clock_dir = os.path.dirname(os.path.realpath(__file__))


class ClockTest(Test):
    def __init__(self):
        Test.__init__(self)

    def test(self):
        """
        Clock test case
        :return:
        """
        result = self.command.run_cmd("%s/clock" % clock_dir)
        if result[2] == 0:
            self.logger.info("Test clock succeed.")
            return True

        self.logger.error("Test clock failed.\n %s" % result[1])
        return False
