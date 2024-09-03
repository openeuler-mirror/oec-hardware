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

import os
import datetime
import argparse
from subprocess import getoutput
from .document import Document, FactoryDocument
from .env import CertEnv
from .command import Command
from .constants import REBOOT_CASE


class Reboot:
    """
    Special for restart tasks, so that the test can be continued after the machine is restarted
    """

    def __init__(self, testname, job, rebootup):
        self.testname = testname
        self.rebootup = rebootup
        self.job = job
        self.reboot = dict()
        self.args = None
        self.logger = None

    def clean(self):
        """
        Remove reboot file
        :return:
        """
        if not (self.job and self.testname):
            return

        for test in self.job.test_factory:
            if test["run"] and self.testname == test["name"]:
                test["reboot"] = False

        os.remove(CertEnv.rebootfile)
        getoutput("systemctl disable oech")

    def setup(self, args=None):
        """
        Reboot  setuping
        :return:
        """
        self.args = args or argparse.Namespace()
        self.logger = getattr(self.args, "test_logger", None)

        if not (self.job and self.testname):
            self.logger.error("Invalid reboot input.")
            return False

        self.job.save_result()
        for test in self.job.test_factory:
            if test["run"] and test["name"] in REBOOT_CASE:
                test["reboot"] = True
                test["status"] = "FAIL"
        if not FactoryDocument(CertEnv.factoryfile, self.logger, self.job.test_factory).save():
            self.logger.error("Save testfactory doc failed before reboot.")
            return False

        reboots = list()
        for test in self.job.test_factory:
            if self.testname == test["name"]:
                reboot = dict()
                reboot["job_id"] = self.job.job_id
                reboot["time"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d%H%M%S")
                reboot["test"] = self.testname
                reboot["rebootup"] = self.rebootup
                reboots.append(reboot)
            elif test["reboot"]:
                reboot = dict()
                reboot["job_id"] = self.job.job_id
                reboot["test"] = test["name"]
                reboots.append(reboot)

        if not Document(CertEnv.rebootfile, self.logger, reboots).save():
            self.logger.error("Save reboot doc failed.")
            return False
        command = Command(self.logger)
        command.run_cmd("systemctl daemon-reload")
        cmd_result = command.run_cmd("systemctl enable oech")
        if len(cmd_result[1]) != 0 and cmd_result[2] != 0:
            self.logger.error(
                "Enable oech.service failed.\n %s" % cmd_result[1])
            return False

        return True

    def check(self, logger=None):
        """
        Reboot file check
        :return:
        """
        if not logger:
            logger = self.logger

        doc = Document(CertEnv.rebootfile, logger)
        if not doc.load():
            logger.error("Reboot file load failed.")
            return False

        try:
            for testcase in doc.document:
                self.reboot = testcase
                if self.reboot.get("rebootup"):
                    self.testname = self.reboot.get("test")
                    self.job.job_id = self.reboot.get("job_id")
                    self.job.logpath = os.path.join(CertEnv.logdirectoy + "/" + self.job.job_id + "/job.log")
                    self.job.subtests_filter = self.reboot.get("rebootup")
                    break
            time_reboot = datetime.datetime.strptime(self.reboot.get("time"), "%Y%m%d%H%M%S")
            test_suite = self.job.test_suite
            reboot_suite = []
            for suit in test_suite:
                if suit.get("reboot"):
                    reboot_suite.append(suit)
            self.job.test_suite = reboot_suite
        except Exception:
            logger.error("Reboot file format not as expect.")
            return False

        time_now = datetime.datetime.now()
        time_delta = (time_now - time_reboot).seconds
        command = Command(logger)
        cmd_result = command.run_cmd(
            "last reboot -s '%s seconds ago' | grep '^reboot .*$'" % time_delta)
        if cmd_result[2] != 0:
            logger.error("Reboot times check failed.")
            return False

        logger.info("Reboot time check : %s" % cmd_result[0])
        return True

