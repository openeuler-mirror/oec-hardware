#!/usr/bin/env python3
# coding: utf-8
# Copyright (c) 2022 Huawei Technologies Co., Ltd.
# oec-hardware is licensed under the Mulan PSL v2.gica's
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Author: yangyulong
# Create: 2024-04-22
# Desc: check srpm version info

import argparse
import csv
import os
import stat
import time
from subprocess import getoutput
import yaml

from hwcompatible.constants import CMP_RESULT_LESS, CMP_RESULT_DIFF
from hwcompatible.test import Test


class SrpmTest(Test):
    def __init__(self):
        Test.__init__(self)
        self.dir_config = os.path.join(os.path.realpath(os.path.dirname(__file__)), 'config')
        self.kernel = getoutput('uname -r')
        self.repo_range = ['source', 'EPOL']

    def setup(self, args=None):
        """
        Initialization before test
        """
        self.args = args or argparse.Namespace()
        self.logger = getattr(self.args, "test_logger", None)

    def query_repo_rpms(self):
        """
        get test repo srpms version info
        @return:
        """
        src_rpms = {}

        for model in self.repo_range:
            cmd = "yum list available | awk '$3 == \"%s\"' " % model
            srpms_repo = getoutput(cmd)
            if not srpms_repo:
                self.logger.error("not query yum repo rpms by model %s, please check the yum config" % model)
            for line in srpms_repo.split("\n"):
                src_info = line.split()
                if len(src_info) != 3:
                    self.logger.debug("abnormal source rpm info line: %s" % line)
                    continue
                src_name = src_info[0].split('.')[0]
                version = src_info[1].split('-')[0].split(':')[-1]
                src_rpms.setdefault(src_name, version)

        return src_rpms

    def get_min_srpms(self):
        """
        get min srpms version info
        @return:
        """
        kernel_version = self.kernel.split('-')[0]
        base_path = os.path.join(self.dir_config, "min_%s.yaml" % kernel_version)
        try:
            with open(base_path, "r") as f:
                base_rpms = yaml.safe_load(f)
        except FileNotFoundError as err:
            return False

        return base_rpms

    @staticmethod
    def dumps_srpm(min_srpms, test_srpms):
        """
        dump test srpms
        @param min_srpms: base min srpms version
        @param test_srpms: test srpms version
        @return:
        """
        all_dumps = []
        for srpm, version in min_srpms.items():
            test_version = test_srpms.get(srpm)
            if test_version is None:
                all_dumps.append([srpm, version, '', CMP_RESULT_LESS])
            else:
                if version == test_version:
                    continue
                all_dumps.append([srpm, version, test_version, CMP_RESULT_DIFF])

        return all_dumps

    def export_diff_result(self, all_dumps):
        """
        export difference srpm version info
        @param all_dumps: difference compare result
        """
        flags = os.O_RDWR | os.O_CREAT
        modes = stat.S_IROTH | stat.S_IRWXU
        report_name = "result_srpms_%s.csv" % time.strftime("%Y%m%d%H%M%S", time.localtime())
        report_output = os.path.join(self.logger.logdir, report_name)
        with os.fdopen(os.open(report_output, flags, modes), 'w+', newline='', encoding='utf-8') as f_in:
            f_csv = csv.writer(f_in)
            f_csv.writerows(all_dumps)

        self.logger.info("test min srpms version details report: %s" % report_output)

    def test(self):
        """
        test current srpms version with base min srpms version
        """
        self.logger.info("Test srpm start.")
        result = True
        min_srpms = self.get_min_srpms()
        if not min_srpms:
            self.logger.error("Test srpm not support kernel version: %s" % self.kernel)
            return False

        test_srpms = self.query_repo_rpms()
        if test_srpms:
            all_dumps = self.dumps_srpm(min_srpms, test_srpms)
            if all_dumps:
                result = False
                result_head = ['srpm', 'base version', 'test version', 'compare result']
                all_dumps.insert(0, result_head)
                self.export_diff_result(all_dumps)
        else:
            result = False
            self.logger.error("Not get yum repo source rpm info.")

        if result:
            self.logger.info("Test srpm succeed.")
        else:
            self.logger.error("Test srpm failed.")

        return result
