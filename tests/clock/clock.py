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

import os

from hwcompatible.test import Test

clock_dir = os.path.dirname(os.path.realpath(__file__))


class ClockTest(Test):
    """
    Clock Test
    """
    def test(self):
        """
        Clock test case
        :return:
        """
        return 0 == os.system("cd %s; ./clock" % clock_dir)


if __name__ == '__main__':
    t = ClockTest()
    t.setup()
    t.test()
