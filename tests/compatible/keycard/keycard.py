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

import os
import shutil
from hwcompatible.test import Test
from hwcompatible.command_ui import CommandUI

keycard_dir = os.path.dirname(os.path.realpath(__file__))


class KeyCardTest(Test):
    def __init__(self):
        Test.__init__(self)
        self.com_ui = CommandUI()
        self.target_file = "/usr/lib64/libswsds.so"

    def test(self):
        """
        Run key card test case
        return: result
        """
        result = True
        original_file = os.path.join(keycard_dir, "libswsds.so")
        shutil.copy(original_file, self.target_file)
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
        self.logger.info("Start to test, please wait.")
        execnum = execnum.split(" ")
        for num in execnum:
            result = self.command.run_cmd(
                "echo %s | %s/TestSDS" % (num, keycard_dir))
            if result[2] != 0:
                result = False

        if result:
            self.logger.info("Test key card succeed.")
        else:
            self.logger.error("Test key card failed.")
        return result
    
    def teardown(self):
        """
        Environment recovery after test
        :return:
        """
        if os.path.exists(self.target_file):
            os.remove(self.target_file)