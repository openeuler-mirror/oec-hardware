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

"""Network Test"""

import os
from urllib.parse import urlencode
from urllib.request import urlopen, Request

from hwcompatible.test import Test
from hwcompatible.command import Command


class NetworkTest(Test):
    """
    :Network Test
    """
    def __init__(self):
        Test.__init__(self)
        self.device = None
        self.requirements = ['ethtool', 'iproute', 'psmisc']
        self.subtests = [self.test_ip_info, self.test_icmp]
        self.interface = None
        self.other_interfaces = []
        self.server_ip = None
        self.server_port = "80"
        self.retries = 3
        self.speed = 1000   # Mb/s
        self.target_bandwidth_percent = 0.8
        self.testfile = 'testfile'

    def set_other_interfaces_up(self):
        """
        Set other interfaces to up
        :return:
        """
        for interface in self.other_interfaces:
            # Not ifup(), as some interfaces may not be linked
            os.system("ip link set up %s" % interface)
        return True

    def get_interface_ip(self):
        """
        Get interface ip
        :return:
        """
        com = Command("ip addr show %s" % self.interface)
        pattern = r".*inet.? (?P<ip>.+)/.*"
        try:
            ip_addr = com.get_str(pattern, 'ip', False)
            return ip_addr
        except Exception:
            self.logger.error("[X] No available ip on the interface.")
        return ""

    def test_icmp(self):
        """
        Test ICMP
        :return:
        """
        count = 500
        com = Command("ping -q -c %d -i 0 %s" % (count, self.server_ip))
        pattern = r".*, (?P<loss>\d+\.{0,1}\d*)% packet loss.*"

        for _ in range(self.retries):
            try:
                self.logger.info(com.command)
                loss = com.get_str(pattern, 'loss', False)
                com.print_output()
            except Exception as concrete_error:
                self.logger.error(concrete_error)
            if float(loss) == 0:
                return True
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
        except Exception as concrete_error:
            self.logger.error(str(concrete_error))
            return False
        self.logger.info("Status: %u %s" % (response.code, response.msg))
        return int(response.code) == 200

    def create_testfile(self):
        """
        Create testfile
        :return:
        """
        bs = 128
        count = self.speed/8
        cmd = "dd if=/dev/urandom of=%s bs=%uk count=%u" % (self.testfile, bs, count)
        return 0 == os.system(cmd)

    def test_ip_info(self):
        """
        Test ip info
        :return:
        """
        if not self.interface:
            self.logger.error("[X] No interface assigned.")
            return False
        self.logger.info("[.] The test interface is %s." % self.interface)

        if not self.server_ip:
            self.logger.error("[X] No server ip assigned.")
            return False
        self.logger.info("[.] The server ip is %s." % self.server_ip)

        client_ip = self.get_interface_ip()
        if not client_ip:
            self.logger.error("[X] No available ip on %s." % self.interface)
            return False
        self.logger.info("[.] The client ip is %s on %s." % (client_ip, self.interface))

        return True
