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
# Create: 2022-05-23

"""InfiniBand Test"""
import argparse
from rdma import RDMATest


class InfiniBandTest(RDMATest):
    """
    InfiniBand Test
    """
    def __init__(self):
        RDMATest.__init__(self)
        self.link_layer = 'InfiniBand'
        self.subtests = [self.test_ip_info, self.test_ibstatus, self.test_ib_link,
                         self.test_icmp, self.test_rdma]
        self.speed = 56000   # Mb/s
        self.target_bandwidth_percent = 0.5
        self.config_data = dict()
        self.server_ip = ""

    def test_ib_link(self):
        """
        IB Link test
        :return:
        """
        if 'LinkUp' not in self.phys_state:
            print("[X] Device is not LinkUp.")

        if 'ACTIVE' not in self.state:
            print("[X] Link is not ACTIVE.")

        if self.base_lid == 0x0:
            print("[X] Fail to get base lid of %s." % self.interface)
            return False
        print("[.] The base lid is %s" % self.base_lid)

        if self.sm_lid == 0x0:
            print("[X] Fail to get subnet manager lid of %s." % self.interface)
            return False
        print("[.] The subnet manager lid is %s" % self.sm_lid)

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
        self.config_data = getattr(self.args, "config_data", None)
        if self.config_data:
            self.server_ip = self.config_data.get("server_ip", "")
        else:
            print("Failed to test item value from configuration file.")
    
    def test(self):
        """
        test case
        :return:
        """
        if not self.server_ip:
            print("Failed to get server ip from configuration file.")
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
        print("[.] Stop all test servers...")
        self.call_remote_server('all', 'stop')

        print("[.] Restore interfaces up...")
        self.set_other_interfaces_up()

        print("[.] Test finished.")
