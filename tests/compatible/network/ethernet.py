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
# Desc: Ethernet test

from rdma import RDMATest


class EthernetTest(RDMATest):
    def __init__(self):
        RDMATest.__init__(self)

    def is_RoCE(self):
        """
        Judge whether ethernet is roce
        :return:
        """
        path_netdev = ''.join(['/sys', self.device.get_property("DEVPATH")])
        path_pci = path_netdev.split('net')[0]
        result = self.command.run_cmd("ls %s | grep -q infiniband" % path_pci, ignore_errors=False)
        if result[2] == 0:
            self.logger.info("Current ethernet supports RoCE.")
            return True
        
        self.logger.info("Current ethernet doesn't support RoCE, no need test Roce.")
        return False

    def setup(self, args=None):
        """
        Initialization before test
        :param args:
        :return:
        """
        super().setup(args)
        if self.is_RoCE():
            if self.choice.lower() == "y":
                self.logger.info(
                    "It will test RoCE interface %s, including rdma test." % self.interface)
                self.link_layer = 'Ethernet'
                self.subtests = [self.test_ip_info, self.test_ibstatus,
                                 self.test_eth_link, self.test_icmp, self.test_rdma]
                return
        self.logger.info("It will test normal ethernet %s." % self.interface)
        self.subtests = [self.test_ip_info, self.test_eth_link, self.test_icmp,
                         self.test_udp_tcp, self.test_http]