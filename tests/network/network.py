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

"""Network Test"""

import os
import time
import base64
from urllib.parse import urlencode
from urllib.request import urlopen, Request

from hwcompatible.test import Test
from hwcompatible.command import Command


class NetworkTest(Test):
    """
    Network Test
    """
    def __init__(self):
        Test.__init__(self)
        self.requirements = ['ethtool', 'iproute', 'psmisc', 'qperf']
        self.retries = 3
        self.testfile = 'testfile'

    def ifdown(self, interface):
        """
        Judge whether the specified interface is closed successfully
        :param interface:
        :return:
        """
        Command("ip link set down %s" % interface).echo()
        for _ in range(5):
            if os.system("ip link show %s | grep 'state DOWN'" % interface) == 0:
                return True
            time.sleep(1)
        return False

    def ifup(self, interface):
        """
        Judge whether the specified interface is enabled successfully
        :param interface:
        :return:
        """
        Command("ip link set up %s" % interface).echo()
        for _ in range(5):
            time.sleep(1)
            if os.system("ip link show %s | grep 'state UP'" % interface) == 0:
                return True
        return False

    def get_speed(self):
        """
        Get speed on the interface
        :return:
        """
        com = Command("ethtool %s" % self.interface)
        pattern = r".*Speed:\s+(?P<speed>\d+)Mb/s"
        try:
            speed = com.get_str(pattern, 'speed', False)
            return int(speed)
        except Exception:
            self.logger.error("[X] No speed found on the interface.")
            return None

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
            return None

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
                if float(loss) == 0:
                    return True
            except Exception as concrete_error:
                self.logger.error(concrete_error)
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
        url = 'http://%s/api/%s' % (self.server_ip, act)
        data = urlencode(form).encode('utf8')
        headers = {
            'Content-type': 'application/x-www-form-urlencoded',
            'Accept': 'text/plain'
        }
        try:
            request = Request(url, data=data, headers=headers)
            response = urlopen(request)
        except Exception as concrete_error:
            self.logger.error(str(concrete_error))
            return False
        self.logger.info("Status: %u %s" % (response.code, response.msg))
        return int(response.code) == 200

    def test_udp_latency(self):
        """
        Test udp latency
        :return:
        """
        cmd = "qperf %s udp_lat" % self.server_ip
        self.logger.info(cmd)
        for _ in range(self.retries):
            if os.system(cmd) == 0:
                return True
        return False

    def test_tcp_latency(self):
        """
        tcp test
        """
        cmd = "qperf %s tcp_lat" % self.server_ip
        self.logger.info(cmd)
        for _ in range(self.retries):
            if os.system(cmd) == 0:
                return True
        return False

    def test_tcp_bandwidth(self):
        """
        Test tcp bandwidth
        :return:
        """
        cmd = "qperf %s tcp_bw" % self.server_ip
        self.logger.info(cmd)
        com = Command(cmd)
        pattern = r"\s+bw\s+=\s+(?P<bandwidth>[\.0-9]+ [MG]B/sec)"
        for _ in range(self.retries):
            try:
                bandwidth = com.get_str(pattern, 'bandwidth', False)
                band_width = bandwidth.split()
                if 'GB' in band_width[1]:
                    bandwidth = float(band_width[0]) * 8 * 1024
                else:
                    bandwidth = float(band_width[0]) * 8

                target_bandwidth = self.target_bandwidth_percent * self.speed
                self.logger.info("Current bandwidth is %.2fMb/s, target is %.2fMb/s" %
                                 (bandwidth, target_bandwidth))
                if bandwidth > target_bandwidth:
                    return True
            except Exception as concrete_error:
                self.logger.error(concrete_error)
        return False

    def create_testfile(self):
        """
        Create testfile
        :return:
        """
        b_s = 128
        count = self.speed/8
        cmd = "dd if=/dev/urandom of=%s bs=%uk count=%u" % (self.testfile, b_s, count)
        return os.system(cmd) == 0

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
        except Exception as concrete_error:
            self.logger.error(concrete_error)
            return False

        form['filename'] = filename
        form['filetext'] = filetext
        url = 'http://%s/api/file/upload' % self.server_ip
        data = urlencode(form).encode('utf8')
        headers = {
            'Content-type': 'application/x-www-form-urlencoded',
            'Accept': 'text/plain'
        }

        time_start = time.time()
        try:
            request = Request(url, data=data, headers=headers)
            response = urlopen(request)
        except Exception as concrete_error:
            self.logger.error(concrete_error)
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
        url = "http://%s/files/%s" % (self.server_ip, filename)

        time_start = time.time()
        try:
            response = urlopen(url)
        except Exception as concrete_error:
            self.logger.error(concrete_error)
            return False
        time_stop = time.time()
        time_download = time_stop - time_start

        self.logger.info("Status: %u %s" % (response.code, response.msg))
        self.logger.info(str(response.headers), terminal_print=False)
        filetext = response.read()
        try:
            with open(self.testfile, 'wb') as file_info:
                file_info.write(filetext)
        except Exception as concrete_error:
            self.logger.error(concrete_error)
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
            self.logger.error("[X] start qperf server failed.")
            return False

        self.logger.info("[+] Testing udp latency...")
        if not self.test_udp_latency():
            self.logger.error("[X] Test udp latency failed.")
            return False

        self.logger.info("[+] Testing tcp latency...")
        if not self.test_tcp_latency():
            self.logger.error("[X] Test tcp latency failed.")
            return False

        self.logger.info("[+] Testing tcp bandwidth...")
        if not self.test_tcp_bandwidth():
            self.logger.error("[X] Test tcp bandwidth failed.")
            return False

        self.call_remote_server('qperf', 'stop')
        return True

    def test_http(self):
        """
        Test http
        :return:
        """
        self.logger.info("[+] Creating testfile to upload...")
        if not self.create_testfile():
            self.logger.error("[X] Create testfile failed.")
            return False

        self.logger.info("[+] Testing http upload(POST)...")
        if not self.test_http_upload():
            self.logger.error("[X] Test http upload failed.")
            return False

        self.logger.info("[+] Testing http download(GET)...")
        if not self.test_http_download():
            self.logger.error("[X] Test http download failed.")
            return False

        return True

    def test_eth_link(self):
        """
        Test eth link
        :return:
        """
        self.logger.info("[+] Setting interface %s down..." % self.interface)
        if not self.ifdown(self.interface):
            self.logger.error("[X] Fail to set interface %s down." % self.interface)
            return False

        self.logger.info("[+] Setting interface %s up..." % self.interface)
        if not self.ifup(self.interface):
            self.logger.error("[X] Fail to set interface %s up." % self.interface)
            return False

        self.speed = self.get_speed()
        if self.speed:
            self.logger.info("[.] The speed of %s is %sMb/s." % (self.interface, self.speed))
        else:
            self.logger.error("[X] Fail to get speed of %s." % self.interface)
            return False

        return True

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

    def tests(self):
        """
        test case
        :return:
        """
        for subtest in self.subtests:
            if not subtest():
                return False
        return True

    def teardown(self):
        """
        Environment recovery after test
        :return:
        """
        self.logger.info("[.] Stop all test servers...")
        self.call_remote_server('all', 'stop')

        self.logger.info("[.] Test finished.")
