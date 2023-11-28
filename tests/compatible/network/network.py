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
# Desc: Network Test

import os
import time
import base64
import argparse
from urllib.parse import urlencode
from urllib.request import urlopen, Request
from hwcompatible.test import Test
from hwcompatible.command import Command
from hwcompatible.constants import FILE_FLAGS, FILE_MODES


class NetworkTest(Test):
    def __init__(self):
        Test.__init__(self)
        self.requirements = ['ethtool', 'iproute', 'psmisc', 'qperf']
        self.device = None
        self.interface = None
        self.server_ip = ""
        self.client_ip = ""
        self.server_port = "80"
        self.config_data = dict()
        self.choice = "N"
        self.retries = 3
        self.speed = 0   # Mb/s
        self.subtests = []
        self.target_bandwidth_percent = 0.75
        self.testfile = 'testfile'
        self.testbw_file = "test_bw.log"

    def setup(self, args=None):
        """
        Initialization before test
        :param args:
        :return:
        """
        self.args = args or argparse.Namespace()
        self.logger = getattr(self.args, "test_logger", None)
        self.command = Command(self.logger)
        self.device = getattr(self.args, 'device', None)
        self.interface = self.device.get_property("INTERFACE")
        self.config_data = getattr(args, "config_data", None)
        if self.config_data:
            self.server_ip = self.config_data.get("server_ip", "")
            self.client_ip = self.config_data.get("client_ip", "")
            if ":" in self.server_ip:
                self.server_ip, self.server_port = self.server_ip.split(":")
            self.choice = self.config_data.get("if_rdma")
        else:
            self.logger.error(
                "Get test item value from configuration file failed.")
            return False

        self.show_driver_info()
        return True

    def test(self):
        """
        test case
        :return:
        """
        if not self.server_ip:
            self.logger.error("Get server ip from configuration file failed.")
            return False

        if not self.check_fibre():
            self.logger.error("Get fibre information failed.")
            return False

        for subtest in self.subtests:
            if not subtest():
                return False
        return True

    def teardown(self):
        """
        Environment recovery after test
        :return:
        """
        self.logger.info("Stop all test servers.")
        self.call_remote_server('all', 'stop', self.server_ip)
        if os.path.exists(self.testfile):
            os.remove(self.testfile)
        if os.path.exists(self.testbw_file):
            os.remove(self.testbw_file)
        ip = self.command.run_cmd(
            "ifconfig %s:0 | grep '.*inet' | awk '{print $2}'" % self.interface)[0]
        if ip:
            self.command.run_cmd(
                "ip addr del %s dev %s:0" % (ip, self.interface))

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

    def ifdown(self, interface):
        """
        Judge whether the specified interface is closed successfully
        :param interface:
        :return:
        """
        self.command.run_cmd("ip link set down %s" % interface)
        for _ in range(10):
            result = self.command.run_cmd(
                "ip link show %s | grep 'state DOWN'" % interface, ignore_errors=False)
            if result[2] == 0:
                self.logger.info("Set interface %s down succeed." % self.interface)
                return True
            time.sleep(1)
            
        self.logger.error("Set interface %s down failed." % self.interface)
        return False

    def ifup(self, interface):
        """
        Judge whether the specified interface is enabled successfully
        :param interface:
        :return:
        """
        self.command.run_cmd("ip link set up %s" % interface)
        for _ in range(20):
            result = self.command.run_cmd(
                "ip link show %s | grep 'state UP'" % interface, ignore_errors=False)
            if result[2] == 0:
                self.logger.info("Set interface %s up succeed." % self.interface)
                return True
            time.sleep(1)

        self.logger.error("Set interface %s up failed." % self.interface)
        return False

    def get_speed(self):
        """
        Get speed on the interface
        :return:
        """
        speed = self.command.run_cmd(
            "ethtool %s | grep Speed | awk '{print $2}'" % self.interface)
        if speed[2] != 0:
            self.logger.error("No speed found on the interface.")
            return 0

        return int(speed[0][:-5])

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
        """
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

    def test_udp_latency(self):
        """
        Test udp latency
        :return:
        """
        cmd = "qperf %s udp_lat" % self.server_ip
        for _ in range(self.retries):
            result = self.command.run_cmd(cmd)
            if result[2] != 0:
                return False
        return True

    def test_tcp_latency(self):
        """
        tcp test
        """
        cmd = "qperf %s tcp_lat" % self.server_ip
        for _ in range(self.retries):
            result = self.command.run_cmd(cmd)
            if result[2] != 0:
                return False
        return True

    def test_tcp_bandwidth(self):
        """
        Test tcp bandwidth
        :return:
        """
        cmd = "qperf %s tcp_bw | grep 'bw' | grep -v 'tcp_bw' | awk '{print $3,$4}'" % self.server_ip
        for _ in range(self.retries):
            result = self.command.run_cmd(cmd)
            if result[2] != 0:
                continue
            band_width = result[0].split()
            if 'GB' in band_width[1]:
                bandwidth = float(band_width[0]) * 8 * 1024
            else:
                bandwidth = float(band_width[0]) * 8

            target_bandwidth = self.target_bandwidth_percent * self.speed
            self.logger.info(
                "Current bandwidth is %.2fMb/s, target is %.2fMb/s" %
                (bandwidth, target_bandwidth))
            if bandwidth > target_bandwidth:
                self.logger.info("Test tcp bandwidth succeed.")
                return True
        return False

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

    def test_http_upload(self):
        """
        Test http upload
        :return:
        """
        form = {}
        size = os.path.getsize(self.testfile)
        filename = os.path.basename(self.testfile)

        try:
            with open(self.testfile, 'rb') as file_info:
                filetext = base64.b64encode(file_info.read())
        except Exception:
            self.logger.error("Encode file %s failed." % self.testfile)
            return False

        form['filename'] = filename
        form['filetext'] = filetext
        url = 'http://%s:%s/api/file/upload' % (
            self.server_ip, self.server_port)
        data = urlencode(form).encode('utf8')
        headers = {
            'Content-type': 'application/x-www-form-urlencoded',
            'Accept': 'text/plain'
        }

        time_start = time.time()
        request = Request(url, data=data, headers=headers)
        try:
            response = urlopen(request)
        except Exception:
            self.logger.error("Open url %s failed." % url)
            return False
        time_stop = time.time()
        time_upload = time_stop - time_start

        self.logger.info("Status: %u %s" % (response.code, response.msg))
        self.logger.info(str(response.headers), terminal_print=False)
        if time_upload != 0:
            self.logger.info("Upload %s in %.2fs, %.2f MB/s" %
                             (filename, time_upload, size/1000000 / time_upload))
        return True

    def test_http_download(self):
        """
        Test http download
        :return:
        """
        filename = os.path.basename(self.testfile)
        url = "http://%s:%s/files/%s" % (self.server_ip,
                                         self.server_port, filename)

        time_start = time.time()
        try:
            response = urlopen(url)
        except Exception:
            self.logger.error("Open url %s failed." % url)
            return False
        time_stop = time.time()
        time_download = time_stop - time_start

        self.logger.info("Status: %u %s" % (response.code, response.msg))
        self.logger.info(str(response.headers), terminal_print=False)
        filetext = response.read()
        try:
            with os.fdopen(os.open(self.testfile, FILE_FLAGS, FILE_MODES),
                           "wb") as file_info:
                file_info.write(filetext)
        except Exception:
            self.logger.error("Write file %s failed." % self.testfile)
            return False

        size = os.path.getsize(self.testfile)
        if time_download != 0:
            self.logger.info("Download %s in %.2fs, %.2f MB/s" %
                             (filename, time_download, size/1000000 / time_download))
        return True

    def test_udp_tcp(self):
        """
        Test udp tcp
        :return:
        """
        if not self.call_remote_server('qperf', 'start'):
            self.logger.error("start qperf server failed.")
            return False

        self.logger.info("Testing udp latency...")
        if not self.test_udp_latency():
            self.logger.error("Test udp latency failed.")
            return False

        self.logger.info("Testing tcp latency...")
        if not self.test_tcp_latency():
            self.logger.error("Test tcp latency failed.")
            return False

        self.logger.info("Testing tcp bandwidth...")
        if not self.test_tcp_bandwidth():
            self.logger.error("Test tcp bandwidth failed.")
            return False

        self.call_remote_server('qperf', 'stop')
        return True

    def test_http(self):
        """
        Test http
        :return:
        """
        self.logger.info("Creating testfile to upload...")
        if not self.create_testfile():
            self.logger.error("Create testfile failed.")
            return False

        self.logger.info("Testing http upload(POST)...")
        if not self.test_http_upload():
            self.logger.error("Test http upload failed.")
            return False

        self.logger.info("Testing http download(GET)...")
        if not self.test_http_download():
            self.logger.error("Test http download failed.")
            return False

        return True

    def test_eth_link(self):
        """
        Test eth link
        :return:
        """
        self.logger.info("Setting interface %s down." % self.interface)
        if not self.ifdown(self.interface):
            return False

        self.logger.info("Setting interface %s up." % self.interface)
        if not self.ifup(self.interface):
            return False

        self.speed = self.get_speed()
        if self.speed:
            self.logger.info("The speed of %s is %sMb/s." %
                             (self.interface, self.speed))
        else:
            self.logger.error("Set speed of %s failed." % self.interface)
            return False

        return True

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
