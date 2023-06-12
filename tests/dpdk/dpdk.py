#!/usr/bin/env python3
# coding: utf-8

# oec-hardware is licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Create: 2020-04-01
# Author: @ylzhangah
# Create: 2022-12-01
# Desc: DPDK test


import os
import argparse
import json
import time
import subprocess

from urllib.parse import urlencode
from urllib.request import urlopen, Request

from hwcompatible.test import Test
from hwcompatible.command import Command
from hwcompatible.document import CertDocument
from hwcompatible.env import CertEnv
from hwcompatible.constants import FILE_FLAGS, FILE_MODES
from hugepages import ShowHugepages


class DPDKTest(Test):
    """
    DPDK test
    """

    def __init__(self):
        Test.__init__(self)
        self.requirements = ["dpdk", "dpdk-tools", "dpdk-devel"]
        self.config_data = dict()
        self.interface = None
        self.server_ip = ""
        self.server_port = 80
        self.portmask = "0xffff"
        self.packet_size = 1514
        self.support_driver = ['mlx4_core', 'mlx5_core', 'ixgbe', 'ice', 'hinic', 'igc']
        self.dpdk_driver = 'uio_pci_generic'
        self.kernel_driver = None
        self.retries = 3
        self.speed = 0   # Mb/s
        self.target_bandwidth_percent = 0.8
        self.device = ""
        self.pci = ""
        self.card_id = None
        self.ethpeer = None
        self.test_dpdk_file = ""

    def setup(self, args=None):
        """
        Initialization before test
        :return:
        """
        self.args = args or argparse.Namespace()
        self.logger = getattr(self.args, "test_logger", None)
        self.command = Command(self.logger)
        self.hugepage = ShowHugepages(self.logger, self.command)
        self.test_dpdk_file = os.path.join(self.logger.logdir, 'test_dpdk.log')
        self.device = getattr(self.args, 'device', None)
        self.interface = self.device.get_property("INTERFACE")
        self.show_driver_info()
        self.pci = self.device.get_pci()
        self.kernel_driver = self.device.get_driver()
        self.card_id = self.device.get_quadruple()
        self.command.run_cmd("dpdk-hugepages.py -u", terminal_print=False)
        self.command.run_cmd("dpdk-hugepages.py -c", terminal_print=False)
        self.command.run_cmd("dpdk-hugepages.py --setup 2G", terminal_print=True)
        self.config_data = getattr(args, "config_data", None)
        self.server_ip = CertDocument(CertEnv.certificationfile, self.logger).get_server()
        self.test_prepare()

    def get_interface_speed(self):
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

    def check_bind(self):
        """
        Check whether binding card is required
        :return:
        """
        # set interface down so that bind the dpdk driver.
        if self.kernel_driver not in self.support_driver:
            self.logger.error("The card driver %s doesn't support dpdk test, Supported drivers are %s."
                              % (self.kernel_driver, self.support_driver))
            return False
        else:
            self.logger.info("DPDK driver is loading...")
            subprocess.getoutput("modprobe uio; modprobe %s" % self.dpdk_driver)
            if self.command.run_cmd("lsmod | grep %s" % self.dpdk_driver, terminal_print=True)[2] != 0:
                self.logger.error("DPDK driver is loaded failed!")
                return False
            else:
                self.logger.info("Get server card's ethpeer...")
                if not self.get_ethpeer():
                    return False
                if self.kernel_driver == "mlx4_core" or self.kernel_driver == "mlx5_core":
                    self.logger.info("The mellanox network card does not need to be bound.")
                    self.command.run_cmd("modprobe -a ib_uverbs mlx5_core mlx5_ib mlx4_core", terminal_print=True)
                else:
                    self.logger.info("Server dpdk is binding...")
                    if not self.server_dpdk_bind():
                        return False
                    self.logger.info("Client dpdk is binding...")
                    if not self.client_dpdk_bind():
                        return False
                return True

    def get_ethpeer(self):
        """
        Get ethpeer.
        :return:
        """
        form = {'serverip': self.server_ip, 'cardid': self.card_id}
        url = 'http://{}:%s/api/get/ethpeer'.format(self.server_ip) % self.server_port
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
        self.logger.info(str(response.headers), terminal_print=False)
        self.ethpeer = json.loads(response.read())['ethpeer']
        self.logger.info("The mac of the server card is %s" % self.ethpeer)
        self.logger.info("Status: %u %s" % (response.code, response.msg))
        if response.code != 200:
            return False
        return True

    def client_dpdk_bind(self):
        """
        Bind client card with dpdk driver
        :return:
        """
        self.logger.info("Setting client interface %s down." % self.interface)
        if not self.ifdown(self.interface):
            self.logger.error("Setting client interface down failed!")
            return False
        else:
            self.logger.info("Client dpdk is binding...")
            cmd = self.command.run_cmd("dpdk-devbind.py -b %s %s" % (self.dpdk_driver, self.interface))
            if cmd[2] == 0:
                self.logger.info("Client dpdk is bound successfully!")
                self.command.run_cmd("dpdk-devbind.py -s")
                return True
            else:
                self.logger.error("Bind card with dpdk driver failed!")
                return False

    def server_dpdk_bind(self):
        """
        Bind the server card.
        :return:
        """
        form = {'serverip': self.server_ip, 'cardid': self.card_id}
        url = 'http://{}:%s/api/bind/server'.format(self.server_ip) % self.server_port
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
        self.logger.info(str(response.headers), terminal_print=False)
        self.logger.info("Status: %u %s" % (response.code, response.msg))
        if response.code != 200:
            return False
        return True

    def test(self):
        """
        Test case
        :return:
        """
        if not self.test_icmp():
            return False

        if not self.check_bind():
            return False

        self.logger.info("Start dpdk-testpmd server...")
        if not self.call_remote_server('dpdk-testpmd', 'start'):
            self.logger.error("[X] start dpdk-testpmd server failed.")
            return False

        self.logger.info("Test dpdk speed...")
        if not self.test_speed():
            self.logger.error("Test dpdk speed failed.")
            return False

        self.logger.info("Stop dpdk-testpmd server...")
        if not self.call_remote_server('dpdk-testpmd', 'stop'):
            self.logger.error("[X] Stop dpdk-testpmd server failed.")
            return False

        return True

    def show_hugepage(self):
        """
        Show Hugepages on system.
        :return:
        """
        if self.hugepage.is_numa():
            self.hugepage.show_numa_pages()
        else:
            self.hugepage.show_non_numa_pages()

    def test_prepare(self):
        """
        Preparation before test
        :return:
        """
        if not self.hugepage.check_hugepage_allocate(self.hugepage.is_numa()):
            self.logger.error("No hugepage allocated.")
            return False

        if not self.hugepage.get_mountpoints():
            self.logger.error("No hugepage mounted.")
            return False

        self.logger.info("Hugepage successfully configured.")
        self.show_hugepage()

        return True

    def test_speed(self):
        """
        Test speed
        :return:
        """
        command = [
            'dpdk-testpmd',
            '-l', '0-1',
            '-n', '1',
            '-a', self.pci,
            '--',
            '--portmask=0x1',
            '--txpkts=%d' % self.packet_size,
            '--rxq=4',
            '--txq=4',
            '--forward-mode=txonly',
            '--eth-peer=0,%s' % self.ethpeer,
            '--stats-period=2'
            ]
        res = subprocess.Popen(command, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.logger.info("Please wait 30 seconds.")
        time.sleep(30)
        res.terminate()
        with os.fdopen(os.open(self.test_dpdk_file, FILE_FLAGS, FILE_MODES), "w") as log:
            log.write(str(res.stdout.read(), 'UTF-8'))
        time.sleep(30)
        res = self.command.run_cmd("grep Tx-bps %s | awk '{print $4}'" % self.test_dpdk_file)
        if res[2] != 0:
            self.logger.error("The test data result is empty, Please check if the server is configured properly!")
        res_list = res[0].split("\n")[-10:-1]
        int_list = [int(x) for x in res_list]
        number = len(int_list)
        if number != 0:
            bandwidth = float(sum(int_list) / number / 1e6)
            # 1e6 = 1000000.0
            target_bandwidth = self.target_bandwidth_percent * self.speed
            self.logger.info("Current bandwidth is around %.2f Mb/s, target is %.2fMb/s" %
                    (bandwidth, target_bandwidth))
            if bandwidth > target_bandwidth:
                self.logger.info("Test dpdk bandwidth successfully.")
                return True
            self.logger.error("Test dpdk bandwidth failed!")
            return False
        else:
            self.logger.error("No data obtained for testing dpdk, Please manually check!")
            return False

    def ifdown(self, interface):
        """
        Judge whether the specified interface is closed successfully
        :param interface:
        :return:
        """
        self.command.run_cmd("ip link set down %s" % interface)
        for _ in range(10):
            result = self.command.run_cmd(
                "ip link show %s | grep 'state DOWN'" % interface, ignore_errors=True)
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
        for _ in range(10):
            result = self.command.run_cmd(
                "ip link show %s | grep 'state UP'" % interface, ignore_errors=True)
            if result[2] == 0:
                self.logger.info("Set interface %s up succeed." % self.interface)
                return True
            time.sleep(1)

        self.logger.error("Set interface %s up failed." % self.interface)
        return False

    def test_icmp(self):
        """
        Test ICMP
        :return:
        """
        self.speed = self.get_interface_speed()
        if self.speed:
            self.logger.info("The speed of %s is %sMb/s." %
                             (self.interface, self.speed))
        else:
            self.logger.error("Set speed of %s failed." % self.interface)

        count = 500
        cmd = "ping -q -c %d -i 0 %s | grep 'packet loss' | awk '{print $6}'" % (
            count, self.server_ip)
        for _ in range(self.retries):
            result = self.command.run_cmd(cmd, ignore_errors=True)
            if result[0].strip() == "0%":
                self.logger.info("Test icmp succeed.")
                return True
        self.logger.error("Test icmp failed.")
        return False

    def call_remote_server(self, cmd, act='start'):
        """
        Connect to the server somehow.
        :param cmd:
        :param act:
        :return:
        """
        form = dict()
        form = {'cmd': cmd, 'serverip': self.server_ip, 'cardid': self.card_id}
        url = 'http://%s/api/%s' % (self.server_ip, act)
        data = urlencode(form).encode('utf8')
        headers = {
            'Content-type': 'application/x-www-form-urlencoded',
            'Accept': 'text/plain'
        }
        request = Request(url, data=data, headers=headers)
        try:
            response = urlopen(request)
        except Exception:
            self.logger.error("Call remote dpdk server url %s failed." % url)
            return False
        self.logger.info("Status: %u %s" % (response.code, response.msg))
        return int(response.code) == 200

    def server_dpdk_unbind(self):
        """
        Unbind the server card.
        :return:
        """
        form = {'serverip': self.server_ip, 'cardid': self.card_id}
        url = 'http://{}/api/unbind/server'.format(self.server_ip)
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
        if response.code != 200:
            return False
        return True

    def dev_unbind(self):
        """
        dpdk unbind
        :return:
        """
        self.logger.info("Unbinding server card...")
        if self.server_dpdk_unbind():
            self.logger.info("Unbind server card successfully!")

        self.logger.info("Unbinding client card...")
        self.command.run_cmd("dpdk-devbind.py -u %s" % self.pci)
        cmd = self.command.run_cmd("dpdk-devbind.py -b %s %s" % (self.kernel_driver, self.pci))
        if cmd[0] == "":
            self.logger.info("Unbinding client card successfully!")

        self.logger.info("Setting client interface %s up..." % self.interface)
        if not self.ifup(self.interface):
            return False
        return True

    def teardown(self):
        """
        Environment recovery after test
        :return:
        """
        if self.kernel_driver == "mlx4_core" or self.kernel_driver == "mlx5_core":
            self.logger.info("The Mellanox card need not unbind！")
        else:
            self.dev_unbind()
        self.call_remote_server('all', 'stop')
        self.logger.info("Stop all test servers.")
