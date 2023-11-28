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
# Desc: Perf Test

import re
from hwcompatible.test import Test


class PerfTest(Test):
    def __init__(self):
        Test.__init__(self)
        self.requirements = ["perf"]
        self.perf_record = "perf record -a -e cycles -o hwcompatible-perf.data sleep 5"
        self.perf_evlist = "perf evlist -i hwcompatible-perf.data"
        self.perf_report = "perf report -i hwcompatible-perf.data --stdio"

    def exec_perf(self):
        """
        Execute perf command
        :return:
        """
        returncode = True
        # record
        self.logger.info("Collecting the perf record.")
        perf_record_echo = self.command.run_cmd(self.perf_record)
        perf_record_macth = re.search("perf record", perf_record_echo[1])
        if not perf_record_macth:
            self.logger.error("Record events failed.")
            returncode = False 
        else:
            self.logger.info("Record events succeed.")

        # evList
        perf_evlist_echo = self.command.run_cmd(self.perf_evlist)
        perf_evlistd_macth = re.search("cycles", perf_evlist_echo[0])
        if not perf_evlistd_macth:
            self.logger.error("Required hardware event available failed because of:\n %s." % perf_evlist_echo[1])
            returncode = False
        else:
            self.logger.info("Hardware event found.")

        # report
        perf_report_echo = self.command.run_cmd(self.perf_report)
        perf_report_macth = re.search(r"\s*\S+\s+(\[\S+.\S+\])\s+\S+", perf_report_echo[0])
        if not perf_report_macth:
            self.logger.error("No samples found. Failed to fetch report because of:\n %s." % perf_report_echo[1])
            returncode = False
        else:
            self.logger.info("Samples found for the hardware event.")
            
        return returncode

    def test(self):
        """
        test case
        :return:
        """
        if self.exec_perf():
            return True
        return False
