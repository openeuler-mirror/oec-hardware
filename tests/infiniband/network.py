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
# Create: 2022-05-23
# Desc: Network Test

import os
import argparse
from urllib.parse import urlencode
from urllib.request import urlopen, Request
from hwcompatible.test import Test
from hwcompatible.command import Command


class NetworkTest(Test):

    def __init__(self):
        Test.__init__(self)
        self.device = None
        self.link_layer = 'InfiniBand'
        self.requirements = ['ethtool', 'iproute', 'psmisc']
        self.subtests = [self.test_ip_info, self.test_ibstatus,
                         self.test_ib_link, self.test_icmp, self.test_rdma]
        self.config_data = None
        self.interface = None
        self.server_ip = None
        self.client_ip = None
        self.server_port = "80"
        self.retries = 3
        self.speed = 1000   # Mb/s
        self.target_bandwidth_percent = 0.8
        self.testfile = 'testfile'

    def setup(self, args=None):
        """
        Initialization before test
        :param args:
        :return:
        """
        self.args = args or argparse.Namespace()
        self.device = getattr(self.args, 'device', None)
        self.interface = self.device.get_property("INTERFACE")
        self.logger = getattr(self.args, "test_logger", None)
        self.command = Command(self.logger)
        self.config_data = getattr(self.args, "config_data", None)
        if not self.config_data:
            self.logger.error(
                "Failed to test item value from configuration file.")
            return False

        self.server_ip = self.config_data.get("server_ip", "")
        self.client_ip = self.config_data.get("client_ip", "")
        if ":" in self.server_ip:
            self.server_ip, self.server_port = self.server_ip.split(":")

        self.show_driver_info()
        return True

    def test(self):
        """
        Test case
        :return:
        """
        if not self.server_ip:
            self.logger.error(
                "Failed to get server ip from configuration file.")
            return False

        if not self.check_fibre():
            self.logger.error("Get fibre information failed.")
            return False

        for subtest in self.subtests:
            if not subtest():
                return False
        return True

    def check_fibre(self):
        """
        Check fibre information
        :return:
        """
        cmd = self.command.run_cmd(
            "ethtool %s | grep 'Port' | awk '{print $2}'" % self.interface)
        port_type = cmd[0].strip()
        if port_type != "FIBRE":
            self.logger.info("The %s port type is %s, skip checking." %
                             (self.interface, port_type))
            return True

        cmd = self.command.run_cmd(
            "ethtool %s | grep 'Speed' | awk '{print $2}'" % self.interface)
        speed = cmd[0].strip()
        if speed == "1000Mb/s":
            self.logger.info("The %s fibre speed is %s, skip checking." %
                             (self.interface, speed))
            return True

        self.logger.info(
            "The %s port type is fibre, next to check fibre." % self.interface)
        cmd = self.command.run_cmd("ethtool -m %s" % self.interface)
        return cmd[2] == 0

    def get_interface_ip(self):
        """
        Get interface ip
        :return:
        """
        com = self.command.run_cmd(
            "ip addr show %s | grep inet | awk '{print $2}' | cut -d '/' -f 1" % self.interface)
        if com[2] != 0:
            self.logger.error("Get available ip on the interface failed.")
            return ""
        return com[0].strip()

    def test_icmp(self):
        """pcipch
        Test ICMP
        :return:
        """
        count = 500
        cmd = "ping -q -c %d -i 0 %s | grep 'packet loss' | awk '{print $6}'" % (
            count, self.server_ip)
        for _ in range(self.retries):
            result = self.command.run_cmd(cmd)
            if result[0].strip() == "0%":
                self.logger.info("Test icmp succeed.")
                return True
        self.logger.error("Test icmp failed.")
        return False

    def call_remote_server(self, cmd, act='start', ib_server_ip=''):
        """
        Call remote server
        :param cmd:
        :param act:
        :param ib_server_ip:
        :return:
        """
        form = dict()
        form['cmd'] = cmd
        form['ib_server_ip'] = ib_server_ip
        url = 'http://%s:%s/api/%s' % (self.server_ip, self.server_port, act)
        data = urlencode(form).encode('utf8')
        headers = {
            'Content-type': 'application/x-www-form-urlencoded',
            'Accept': 'text/plain'
        }

        request = Request(url, data=data, headers=headers)
        try:
            response = urlopen(request)
        except Exception:
            self.logger.error("Call remote server url %s failed." % url)
            return False
        self.logger.info("Status: %u %s" % (response.code, response.msg))
        return int(response.code) == 200

    def create_testfile(self):
        """
        Create testfile
        :return:
        """
        b_s = 128
        count = self.speed/8
        cmd = self.command.run_cmd(
            "dd if=/dev/urandom of=%s bs=%uk count=%u" % (self.testfile, b_s, count))
        return cmd[2] == 0

    def test_ip_info(self):
        """
        Test ip info
        :return:
        """
        if not self.interface:
            self.logger.error("No interface assigned.")
            return False
        self.logger.info("The test interface is %s." % self.interface)

        if not self.server_ip:
            self.logger.error("No server ip assigned.")
            return False
        self.logger.info("The server ip is %s." % self.server_ip)

        if not self.client_ip:
            self.logger.error("No available ip on %s." % self.interface)
            return False
        self.logger.info("The client ip is %s on %s." %
                         (self.client_ip, self.interface))

        return True
