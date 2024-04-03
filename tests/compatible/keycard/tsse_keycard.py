#!/usr/bin/env python3
# coding: utf-8

# Copyright (c) 2024 Montage Technology.
# oec-hardware is licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Create: 2024-03-20

import argparse
import ssl
import os
from hwcompatible.command import Command
from hwcompatible.test import Test

local_openssl_dir = os.path.dirname(os.path.realpath(__file__))


class TSSEKeyCardTest(Test):
    def __init__(self):
        Test.__init__(self)
        self.device = None

    def setup(self, args=None):
        """
        Initialization before test
        :return:
        """
        self.args = args or argparse.Namespace()
        self.logger = getattr(self.args, "test_logger", None)
        self.command = Command(self.logger)
        self.device = getattr(self.args, 'device', None)
        self.show_driver_info()

    def test(self):
        """
        Run openssl
        return: result
        """
        ret = True
        version = ssl.OPENSSL_VERSION_INFO
        system_openssl = True

        if version < (3, 0):
            self.logger.info("System openssl version is less than 3.0, will install a new one.")
            system_openssl = False
            result = self.command.run_cmd(
                "bash {}/test_tsse_keycard.sh".format(local_openssl_dir))
            if result[2] != 0:
                self.logger.error("failed to install new openssl.")
                return False
            else:
                out = self.command.run_cmd("/opt/local/ssl/bin/openssl version -m")
                self.logger.info(out[0])
        else:
            out = self.command.run_cmd("openssl version -m")
            self.logger.info(out[0])
        self.logger.info("Please make sure the provider shared object file of Mont-TSSE exists in MODULESDIR")

        algorithms = ["aes-128-gcm", "aes-256-gcm", "sha256", "sha384", "sha512",
                    "sm3", "sm4-cbc", "sm4-gcm", "sm2"]
        if system_openssl:
            cmd_format = "openssl speed -provider {} -elapsed {}{}"
        else:
            cmd_format = "/opt/local/ssl/bin/openssl speed -provider {} -elapsed {}{}"

        for alg in algorithms:
            if (alg == "sm2"):
                cmd = cmd_format.format("mcpprovider", "", alg)
            else:
                cmd = cmd_format.format("mcpprovider", "-evp ", alg)
            result = self.command.run_cmd(cmd)
            if result[2] != 0:
                self.logger.error("openssl {} failed.".format(alg))
                self.logger.error(result[1])
                ret = False
            else:
                self.logger.info("openssl {} succeed.".format(alg))

        if ret:
            self.logger.info("Test OpenSSL succeed.")
        else:
            self.logger.error("Test OpenSSL failed.")
        return ret