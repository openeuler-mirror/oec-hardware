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

"""public key card test"""

import os
import subprocess

from hwcompatible.command import Command, CertCommandError
from hwcompatible.test import Test
from hwcompatible.command_ui import CommandUI

keycard_dir = os.path.dirname(os.path.realpath(__file__))


class KeyCardTest(Test):
    """
    Key card Test
    """

    def __init__(self):
        Test.__init__(self)
        self.logpath = None
        self.com_ui = CommandUI()

    def setup(self, args=None):
        """
        Initialization before test
        """
        self.args = args or argparse.Namespace()
        self.name = getattr(args, "testname", "keycard")
        self.logpath = getattr(args, "logdir", None) + "/" + self.name + ".log"

    def test(self):
        """
        Run key card test case
        return: result
        """
        result = True
        ui_message_list = [
            "Which test suite would you like to test: ",
            "1|基本函数测试",
            "2|RSA非对称密码运算函数测试",
            "3|ECC非对称密码运算函数测试",
            "4|对称密码运算函数测试",
            "5|杂凑运算函数测试",
            "6|用户文件操作函数测试",
            "Enter space to split(ex: 1 2 3)\n"
        ]
        ui_message = "\n".join(ui_message_list)
        execnum = self.com_ui.prompt(ui_message)
        print("Start to test, please wait...")
        execnum = execnum.split(" ")
        for num in execnum:
            if os.system("cd %s; echo %s | ./TestSDS &>> %s" % (keycard_dir, num, self.logpath)) != 0:
                result = False

        if result:
            print("Test key card succeed.")
        else:
            print("Test key card failed.")
        return result


if __name__ == '__main__':
    t = KeyCardTest()
    t.setup()
    t.test()
