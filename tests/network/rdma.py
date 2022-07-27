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

"""RDMA Test"""

import os
import re
import argparse
from subprocess import getstatusoutput

from builtins import input
from hwcompatible.command import Command
from hwcompatible.document import CertDocument
from hwcompatible.env import CertEnv
from network import NetworkTest


class RDMATest(NetworkTest):
    """
    RDMA Test
    """
    def __init__(self):
        NetworkTest.__init__(self)
        self.args = None
        self.cert = None
        self.device = None
        self.requirements = ['perftest', 'opensm', 'infiniband-diags',
                             'librdmacm-utils', 'libibverbs-utils']
        self.subtests = [self.test_ibstatus, self.test_icmp, self.test_rdma]
        self.interface = None
        self.ib_device = None
        self.ib_port = None
        self.gid = None
        self.base_lid = None
        self.sm_lid = None
        self.state = None
        self.phys_state = None
        self.link_layer = None
        self.server_ip = None
        self.speed = None   # Mb/s
        self.target_bandwidth_percent = 0.5

    def get_ibstatus(self):
        """
        Get ibstatus
        :return:
        """
        path_netdev = ''.join(['/sys', self.device.get_property("DEVPATH")])
        path_pci = path_netdev.split('net')[0]
        path_ibdev = 'infiniband_verbs/uverb*/ibdev'
        path_ibdev = ''.join([path_pci, path_ibdev])
        cmd = "cat %s" % path_ibdev
        com = Command(cmd)
        try:
            self.ib_device = com.read()
        except Exception as concrete_error:
            self.logger.error(concrete_error)
            return False

        path_ibport = '/sys/class/net/%s/dev_id' % self.interface
        cmd = "cat %s" % path_ibport
        com = Command(cmd)
        try:
            self.ib_port = int(com.read(), 16) + 1
        except Exception as concrete_error:
            self.logger.error(concrete_error)
            return False

        ib_str = "Infiniband device '%s' port %d" % (self.ib_device, self.ib_port)
        self.logger.info("Interface %s ===> %s" % (self.interface, ib_str))

        cmd = "ibstatus"
        self.logger.info(cmd)
        com = Command(cmd)
        try:
            output = com.read()
            for info in output.split('\n\n'):
                if ib_str not in info:
                    continue
                self.logger.info(info)
                self.gid = re.search(r"default gid:\s+(.*)", info).group(1)
                self.base_lid = re.search(r"base lid:\s+(.*)", info).group(1)
                self.sm_lid = re.search(r"sm lid:\s+(.*)", info).group(1)
                self.state = re.search(r"state:\s+(.*)", info).group(1)
                self.phys_state = re.search(r"phys state:\s+(.*)", info).group(1)
                self.link_layer = re.search(r"link_layer:\s+(.*)", info).group(1)
                self.speed = int(re.search(r"rate:\s+(\d*)", info).group(1)) * 1024
        except Exception as concrete_error:
            self.logger.error(concrete_error)
            return False

        return True

    def test_rping(self):
        """
        Test rping
        :return:
        """
        if not self.call_remote_server('rping', 'start', self.server_ip):
            self.logger.info("Start rping server failed.")
            return False

        cmd = "rping -c -a %s -C 50 -v" % self.server_ip
        self.logger.info(cmd)
        if getstatusoutput(cmd)[0] == 0:
            return True
        else:
            self.call_remote_server('rping', 'stop')
            return False

    def test_rcopy(self):
        """
        Test rcopy
        :return:
        """
        if not self.call_remote_server('rcopy', 'start', self.server_ip):
            self.logger.error("Start rcopy server failed.")
            return False

        cmd = "rcopy %s %s" % (self.testfile, self.server_ip)
        self.logger.info(cmd)
        ret = os.system(cmd)
        self.call_remote_server('rcopy', 'stop')
        return ret == 0

    def test_bw(self, cmd):
        """
        Test bandwidth
        :param cmd:
        :return:
        """
        if self.link_layer == 'Ethernet':
            cmd = cmd + ' -R'

        if not self.call_remote_server(cmd, 'start', self.server_ip):
            self.logger.error("Start %s server failed." % cmd)
            return False

        cmd = "%s %s -d %s -i %s" % (cmd, self.server_ip, self.ib_device, self.ib_port)
        self.logger.info(cmd)
        com = Command(cmd)
        pattern = r"\s+(\d+)\s+(\d+)\s+([\.\d]+)\s+(?P<avg_bw>[\.\d]+)\s+([\.\d]+)"
        try:
            avg_bw = com.get_str(pattern, 'avg_bw', False)   # MB/sec
            avg_bw = float(avg_bw) * 8

            tgt_bw = self.target_bandwidth_percent * self.speed
            self.logger.info("Current bandwidth is %.2fMb/s, target is %.2fMb/s"
                             % (avg_bw, tgt_bw))
            return avg_bw > tgt_bw
        except Exception as concrete_error:
            self.logger.error(concrete_error)
            self.call_remote_server(cmd, 'stop')
            return False

    def test_rdma(self):
        """
        Test Remote Direct Memory Access
        :return:
        """
        self.logger.info("[+] Testing rping...")
        if not self.test_rping():
            self.logger.error("[X] Test rping failed.")
            return False

        self.logger.info("[+] Creating testfile to upload...")
        if not self.create_testfile():
            self.logger.error("[X] Create testfile failed.")
            return False

        self.logger.info("[+] Testing rcopy...")
        if not self.test_rcopy():
            self.logger.error("[X] Test rcopy failed.")
            return False

        self.logger.info("[+] Testing ib_read_bw...")
        if not self.test_bw('ib_read_bw'):
            self.logger.error("[X] Test ib_read_bw failed.")
            return False

        self.logger.info("[+] Testing ib_write_bw...")
        if not self.test_bw('ib_write_bw'):
            self.logger.error("[X] Test ib_write_bw failed.")
            return False

        self.logger.info("[+] Testing ib_send_bw...")
        if not self.test_bw('ib_send_bw'):
            self.logger.error("[X] Test ib_send_bw failed.")
            return False

        return True

    def test_ibstatus(self):
        """
        Test ibstatus
        :return:
        """
        if os.system("systemctl start opensm") != 0:
            self.logger.error("[X] start opensm failed.")
            return False

        if os.system("modprobe ib_umad") != 0:
            self.logger.error("[X] modprobe ib_umad failed.")
            return False

        if not self.get_ibstatus():
            self.logger.error("[X] Get status of InfiniBand/RoCE devices failed.")
            return False

        return True

    def setup(self, args=None):
        """
        Initialization before test
        :param args:
        :return:
        """
        self.args = args or argparse.Namespace()
        self.device = getattr(self.args, 'device', None)
        self.interface = self.device.get_property("INTERFACE")

        self.cert = CertDocument(CertEnv.certificationfile, self.logger)
        self.server_ip = self.cert.get_server()

    def test(self):
        """
        test case
        :return:
        """
        message = "Please enter the IP of InfiniBand interface on remote server: \
                   (default %s)\n> " % self.server_ip
        self.server_ip = input(message) or self.server_ip
        
        return self.tests()
