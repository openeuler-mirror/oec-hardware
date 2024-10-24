#!/usr/bin/env python3
# coding: utf-8

# Copyright (c) 2022 Huawei Technologies Co., Ltd.
# oec-hardware is licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Author: @cuixucui
# Create: 2022-09-02

import time
import hashlib
from urllib.parse import urlencode
from urllib.request import urlopen, Request

from .command import Command
from .document import CertDocument
from .env import CertEnv
from .command_ui import CommandUI


class ConfigIP:
    """
     Configure the IP address of the client and server ports
    """

    def __init__(self, config_data, logger, testcase):
        """
        Initialize the ConfigIP object with configuration data, logger, and testcase.

        :param config_data: Configuration data dictionary.
        :param logger: Logger object for logging messages.
        :param testcase: Test case object
        """
        self.config_data = config_data
        self.logger = logger
        self.command = Command(self.logger)
        self.client_ip = ""
        self.server_ip = ""
        self.service_ip = ""
        self.device = ""
        self.client_mac = ""
        self.testcase = testcase

    def config_ip(self):
        """
        Configure the IP address on the network card port.
        """
        cert = CertDocument(CertEnv.certificationfile, self.logger)
        self.service_ip = cert.get_server()

        self.device = self.config_data.get("device", "")
        if not self.device:
            self.logger.error(
                "Get the device failed from the configuration file.")
            return False

        if self.get_port_status():
            self.logger.error("%s port is down." % self.device)
            return False

        # If the client has configured the IP address, obtain the server
        # IP address from the configuration file.
        self.get_ip()
        if self.client_ip:
            self.logger.info("The client IP address already configured.")
            if self.server_ip and self.ping_ip(self.server_ip):
                self.config_data["client_ip"] = self.client_ip
                return True
            self.client_ip = ""
            self.server_ip = ""
            self.logger.info("Generate IP due to invalid server ip.")

        # If the client does not configured an IP address, obtain the IP
        # of the client and server from the configuration file.
        client_ip = self.config_data.get("client_ip", "")
        server_ip = self.config_data.get("server_ip", "")
        if client_ip and server_ip:
            self.logger.info(
                "Configure IP obtained from the configuration file.")
            self.client_ip = client_ip
            self.server_ip = server_ip

        if not self.client_ip or not self.server_ip:
            self.logger.info("Start generating IP address...")
            self.generate_ip()

        # Configure the IP addresses of the client and server.
        if self.client_ip and self.server_ip:
            if not self.config_client_ip():
                self.logger.error("Configure the client ip address failed.")
                return False
            if not self.config_server_ip():
                self.logger.error("Configure the server ip address failed.")
                return False
        else:
            self.logger.error("Generate ip failed")
            return False

        return True

    def get_port_status(self):
        """
        Get the port with up status.
        """
        result = self.command.run_cmd(
            "ip link show %s | grep 'state UP'" % self.device)
        return result[2]

    def get_ip(self):
        """
        Obtain the IP address and MAC address of the client and the IP
        address of the server.
        """
        self.client_ip = self.command.run_cmd(
            "ifconfig %s | grep '.*inet' | awk '{print $2}'" % self.device)[0]
        self.client_mac = self.command.run_cmd(
            "ifconfig %s | grep '.*ether' | awk '{print $2}'" % self.device)[0]
        self.server_ip = self.config_data.get('server_ip', '')

    def generate_ip(self):
        """
        Generate IP addresses of clients and servers.
        """
        self.client_ip = ""
        self.server_ip = ""
        v4network = self.generate_network(self.client_mac)
        num = 2
        while True:
            ip = v4network + '.' + str(num)
            if not self.ping_ip(ip):
                if not self.client_ip:
                    self.client_ip = ip
                else:
                    self.server_ip = ip
            if self.client_ip and self.server_ip:
                self.config_data["client_ip"] = self.client_ip
                self.config_data["server_ip"] = self.server_ip
                break
            num += 1

    def config_client_ip(self):
        """
        Configure the IP address of the client.
        """
        result = CommandUI().prompt_confirm(
            "Are you sure to configure %s on port %s?" % (
                self.client_ip, self.device))

        if result:
            self.command.run_cmd(
                "ifconfig %s:0 %s\/24" % (self.device, self.client_ip))
            return True
        self.logger.warning(
            "User won't use the generate IP address, stop the test.")
        return False

    def config_server_ip(self):
        """
         Configure the IP address of the server.
        """
        result = CommandUI().prompt_confirm(
            "Are you sure to configure %s on server port?\n"
            "After the test, need to manually delete this ip." % self.server_ip)
        if not result:
            self.logger.warning(
                "User won't use the generate IP address, stop the test.")
            return False

        card_id = self.testcase.quad

        form = {'serverip': self.server_ip, 'cardid': card_id}

        url = 'http://{}/api/config/ip'.format(self.service_ip)
        data = urlencode(form).encode('utf8')
        headers = {
            'Content-type': 'application/x-www-form-urlencoded',
            'Accept': 'text/plain'
        }
        try:
            req = Request(url, data=data, headers=headers)
            res = urlopen(req)
            if res.code != 200:
                return False
            return True
        except Exception as e:
            self.logger.error("Upload file to server failed.")
            return False

    def ping_ip(self, ip):
        """
        Determine whether the IP address can be pinged.
        """
        count = 1
        cmd = "ping -q -c %d -W 1 %s | grep 'packet loss' | awk '{print $6}'"\
              % (count, ip)
        result = self.command.run_cmd(cmd)
        if result[0].strip() == "0%":
            return True
        return False

    def generate_network(self, mac):
        """
        Generate the first three IP addresses according to the mac and time.
        """
        while True:
            now_time = str(time.time())
            ip0 = self._str_to_netip(mac + now_time, maxnum=223)
            ip1 = self._str_to_netip(mac)
            ip2 = self._str_to_netip(now_time)
            ip = "%d.%d.%d" % (ip0, ip1, ip2)
            if ip0 <= 223 and ip0 != 127:
                return ip

    @staticmethod
    def _str_to_netip(strs, maxnum=255):
        """
        Generate each value of IP address.
        """
        ipn = int(hashlib.sha512(strs.encode('utf-8')).hexdigest(), 16) % maxnum
        return ipn
