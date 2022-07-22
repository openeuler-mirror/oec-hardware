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

"""Perf Test"""

import re
from hwcompatible.test import Test
from hwcompatible.command import Command


class PerfTest(Test):
    """
    Perf Test
    """
    def __init__(self):
        Test.__init__(self)
        self.requirements = ["perf"]
        self.perfRecord = "perf record -a -e cycles -o hwcompatible-perf.data sleep 5"
        self.perfEvlist = "perf evlist -i hwcompatible-perf.data"
        self.perfReport = "perf report -i hwcompatible-perf.data --stdio"

    def exec_perf(self):
        """
        Execute perf command
        :return:
        """
        # record
        self.logger.info("Collecting the perf record using the command '%s'." % self.perfRecord)
        perfRecordEcho = Command(self.perfRecord).read()
        perfRecordMacth = re.search("perf record", perfRecordEcho)
        if not perfRecordMacth:
            self.logger.error("Failed to record events because of :\n %s." % perfRecordEcho)
        else:
            self.logger.info("Success to record events :\n %s." % perfRecordEcho)

        # evList
        perfEvlistEcho = Command(self.perfEvlist).read()
        perfEvlistdMacth = re.search("cycles", perfEvlistEcho)
        if not perfEvlistdMacth:
            self.logger.error("Required hardware event not available because of :\n %s." % perfEvlistEcho)
            return False
        else:
            self.logger.info("Hardware event found : \n %s." % perfEvlistEcho)

        # report
        perfReportEcho = Command(self.perfReport).read()
        perfReportMacth = re.search(r"\s*\S+\s+(\[\S+.\S+\])\s+\S+", perfReportEcho)
        if not perfReportMacth:
            self.logger.error("No samples found. Failed to fetch report because of:\n %s." % perfReportEcho)
            return False
        else:
            self.logger.info("Samples found for the hardware event :\n %s." % perfReportEcho)
        return True

    def test(self):
        """
        test case
        :return:
        """
        if not self.exec_perf():
            return False
        return True
