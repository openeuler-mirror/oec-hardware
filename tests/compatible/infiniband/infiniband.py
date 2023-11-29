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
# Create: 2022-05-24
# Desc: InfiniBand Test

from tests.compatible.network.rdma import RDMATest


class InfiniBandTest(RDMATest):
    def __init__(self):
        RDMATest.__init__(self)
        self.subtests = [self.test_ip_info, self.test_ibstatus,
                         self.test_ib_link, self.test_icmp, self.test_rdma]

    def test_ib_link(self):
        """
        IB Link test
        :return:
        """
        if 'LinkUp' not in self.phys_state:
            self.logger.error("Device is not LinkUp.")

        if 'ACTIVE' not in self.state:
            self.logger.error("Link is not ACTIVE.")

        if self.base_lid == 0x0:
            self.logger.error("Fail to get base lid of %s." % self.interface)
            return False
        self.logger.info("The base lid is %s." % self.base_lid)

        if self.sm_lid == 0x0:
            self.logger.error(
                "Fail to get subnet manager lid of %s." % self.interface)
            return False
        self.logger.info("The subnet manager lid is %s." % self.sm_lid)

        return True
