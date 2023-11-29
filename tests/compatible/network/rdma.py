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
# Desc: RDMA Test

import os
import re
from tests.compatible.network.network import NetworkTest


class RDMATest(NetworkTest):
    def __init__(self):
        NetworkTest.__init__(self)
        self.requirements += ['perftest', 'opensm', 'rdma-core']
        self.ib_device = None
        self.ib_port = None
        self.link_layer = None
        self.base_lid = None
        self.sm_lid = None
        self.state = None
        self.phys_state = None
        self.speed = 56000  # Mb/s
        self.target_bandwidth_percent = 0.5

    def get_ibstatus(self):
        """
        Get ibstatus
        :return:
        """
        if not self.get_ibdev_ibport():
            return False
        ib_str = "Infiniband device '%s' port %d" % (
            self.ib_device, self.ib_port)
        self.logger.info("Interface %s ===> %s" % (self.interface, ib_str))

        cmd = self.command.run_cmd("ibstatus")
        if cmd[2] != 0:
            self.logger.error("Execute ibstatus failed.")
            return False

        for info in cmd[0].split('\n\n'):
            if ib_str not in info:
                continue
            self.base_lid = re.search(r"base lid:\s+(.*)", info).group(1)
            self.sm_lid = re.search(r"sm lid:\s+(.*)", info).group(1)
            self.state = re.search(r"state:\s+(.*)", info).group(1)
            self.phys_state = re.search(r"phys state:\s+(.*)", info).group(1)
            self.link_layer = re.search(r"link_layer:\s+(.*)", info).group(1)
            self.speed = int(re.search(r"rate:\s+(\d*)", info).group(1)) * 1024
        return True

    def test_rping(self):
        """
        Test rping
        :return:
        """
        if not self.call_remote_server('rping', 'start', self.server_ip):
            self.logger.info("Start rping server failed.")
            return False

        cmd = self.command.run_cmd("rping -c -a %s -C 50 -v" % self.server_ip)
        if cmd[2] == 0:
            return True

        self.call_remote_server('rping', 'stop', self.server_ip)
        return False

    def test_rcopy(self):
        """
        Test rcopy
        :return:
        """
        if not self.call_remote_server('rcopy', 'start', self.server_ip):
            self.logger.error("Start rcopy server failed.")
            return False

        cmd = self.command.run_cmd("rcopy %s %s" %
                                   (self.testfile, self.server_ip))
        if cmd[2] == 0:
            return True
        self.call_remote_server('rcopy', 'stop', self.server_ip)
        return False

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
        get_info = self.command.run_cmd(
            "%s %s -d %s -i %s | tee %s" % (cmd, self.server_ip, self.ib_device, self.ib_port, self.testbw_file))
        if get_info[2] != 0:
            self.logger.error("Test bandwidth %s failed." % cmd)
            self.call_remote_server(cmd, 'stop', self.server_ip)
            return False
        result = self.command.run_cmd(
            "grep -A 1 'BW average' %s | awk '{print $4}' | grep -v 'sec'" % self.testbw_file)
        avg_bw = float(result[0]) * 8
        tgt_bw = self.target_bandwidth_percent * self.speed
        self.logger.info("Current bandwidth is %.2fMb/s, target is %.2fMb/s"
                         % (avg_bw, tgt_bw))
        return avg_bw > tgt_bw

    def test_rdma(self):
        """
        Test Remote Direct Memory Access
        :return:
        """
        self.logger.info("Testing rping...")
        if not self.test_rping():
            self.logger.error("Test rping failed.")
            return False

        self.logger.info("Creating testfile to upload...")
        if not self.create_testfile():
            self.logger.error("Create testfile failed.")
            return False

        self.logger.info("Testing rcopy...")
        if not self.test_rcopy():
            self.logger.error("Test rcopy failed.")
            return False

        self.logger.info("Testing ib_read_bw...")
        if not self.test_bw('ib_read_bw'):
            self.logger.error("Test ib_read_bw failed.")
            return False

        self.logger.info("Testing ib_write_bw...")
        if not self.test_bw('ib_write_bw'):
            self.logger.error("Test ib_write_bw failed.")
            return False

        self.logger.info("Testing ib_send_bw...")
        if not self.test_bw('ib_send_bw'):
            self.logger.error("Test ib_send_bw failed.")
            return False

        return True

    def test_ibstatus(self):
        """
        Test ibstatus
        :return:
        """
        cmd = self.command.run_cmd("systemctl start opensm")
        if cmd[2] != 0:
            self.logger.error("Start opensm failed.")
            return False

        cmd = self.command.run_cmd("modprobe ib_umad")
        if cmd[2] != 0:
            self.logger.error("Try to modprobe ib_umad failed.")
            return False

        if not self.get_ibstatus():
            self.logger.error("Get status of InfiniBand/RoCE devices failed.")
            return False

        return True

    def get_ibdev_ibport(self):
        """
        Get the drive and port of IB card
        :return:
        """
        path_netdev = ''.join(['/sys', self.device.get_property("DEVPATH")])
        path_pci = path_netdev.split('net')[0]
        path_ibdev = os.path.join(path_pci, "infiniband_verbs")
        ibdev_name = self.command.run_cmd("ls %s" % path_ibdev)
        path_ibdev = os.path.join(path_ibdev, ibdev_name[0].strip())
        cmd = self.command.run_cmd("cat %s/ibdev" % path_ibdev)
        if cmd[2] != 0:
            self.logger.error("Get %s failed." % path_ibdev)
            return False
        self.ib_device = cmd[0].strip()

        path_ibport = '/sys/class/net/%s/dev_id' % self.interface
        cmd = self.command.run_cmd("cat %s" % path_ibport)
        if cmd[2] != 0:
            self.logger.error("Get %s failed." % path_ibport)
            return False
        self.ib_port = int(cmd[0], 16) + 1
        return True


