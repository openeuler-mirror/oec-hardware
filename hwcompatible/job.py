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
import sys
import string
import random
import argparse
import yaml

from .test import Test
from .env import CertEnv
from .command import Command, CertCommandError
from .log import Logger
from .reboot import Reboot
from .constants import *


class Job():
    """
    Test task management
    """

    def __init__(self, args=None):
        """
        Creates an instance of Job class.

        :param args: the job configuration, usually set by command
                     line options and argument parsing
        :type args: :class:`argparse.Namespace`
        """
        self.args = args or argparse.Namespace()
        self.test_factory = getattr(self.args, "test_factory", [])
        self.test_suite = getattr(self.args, "test_suite", None)
        self.subtests_filter = getattr(self.args, "subtests_filter", None)
        self.job_id = ''.join(random.sample(
            string.ascii_letters + string.digits, 10))
        self.logpath = CertEnv.logdirectoy + "/" + self.job_id+"/job.log"
        self.config_info = {}
        self.logger = Logger("job.log", self.job_id, sys.stdout, sys.stderr)
        self.total_count = 0
        self.current_num = 0

    def check_test_depends(self):
        """
        Install  dependency packages
        :return: depending
        """
        required_rpms = []
        for tests in self.test_suite:
            for pkg in tests[TEST].requirements:
                cmd = Command("rpm -q %s " % pkg)
                cmd.run(ignore_errors=True)
                return_code = cmd.get_returncode()
                if return_code != 0 and pkg not in required_rpms:
                    required_rpms.append(pkg)

        if required_rpms:
            self.logger.info("Start to install required packages: %s" %
                             ", ".join(required_rpms))
            try:
                cmd = Command("yum install -y %s &>> %s" %
                              (" ".join(required_rpms), self.logpath))
                cmd.echo()
            except CertCommandError as concrete_error:
                self.logger.error("Fail to install required packages.")
                concrete_error.print_errors()
                return False

        return True

    def run_tests(self, subtests_filter=None):
        """
        Start testing
        :param subtests_filter:
        :return:
        """
        if not len(self.test_suite):
            self.logger.warning("No test selected to run.")
            return

        self.get_config()
        self.test_suite.sort(key=lambda k: k[TEST].pri)
        for testcase in self.test_suite:
            config_data = self.get_device(testcase)
            if self._run_test(testcase, config_data, subtests_filter):
                testcase[STATUS] = PASS
                self.logger.info("Test %s succeed." %
                                 testcase[NAME], terminal_print=False)
            else:
                testcase[STATUS] = FAIL
                self.logger.error("Test %s failed." %
                                  testcase[NAME], terminal_print=False)

    def run(self):
        """
        Test entrance
        :return:
        """
        self.logger.start()
        self.current_num = 0
        self.total_count = len(self.test_suite)
        if not self.check_test_depends():
            self.logger.error(
                "Required rpm package not installed, test stopped.")
        else:
            self.run_tests(self.subtests_filter)
        self.save_result()
        self.show_summary()
        self.logger.stop()

    def show_summary(self):
        """
        Command line interface display summary
        :return:
        """
        self.logger.info(
            "-----------------  Summary -----------------", log_print=False)
        for test in self.test_factory:
            if not test[RUN]:
                continue
            name = test[NAME]
            if test[DEVICE].get_name():
                name = test[NAME] + "-" + test[DEVICE].get_name()
            if test[STATUS] == PASS:
                self.logger.info(name.ljust(
                    40) + "\033[0;32mPASS\033[0m", log_print=False)
            else:
                self.logger.info(name.ljust(
                    40) + "\033[0;31mFAIL\033[0m", log_print=False)

    def save_result(self):
        """
        Get test status
        :return:
        """
        for test in self.test_factory:
            for testcase in self.test_suite:
                if test[NAME] == testcase[NAME] and test[DEVICE].path == \
                        testcase[DEVICE].path:
                    test[STATUS] = testcase[STATUS]

    def get_config(self):
        """
        get configuration file
        """
        yaml_file = CertEnv.configfile
        if not os.path.exists(yaml_file):
            self.logger.error("Failed to get configuration file information.")
            return False
        try:
            with open(yaml_file, 'r', encoding="utf-8") as file:
                file_data = file.read()
                self.config_info = yaml.safe_load(file_data)
        except yaml.scanner.ScannerError:
            self.logger.error(
                "The yaml file %s format is error." % yaml_file)
            return False

        return True

    def get_device(self, testcase):
        """
        Get the board configuration information to be tested
        """
        types = testcase[NAME]
        device_name = testcase[DEVICE].get_name()
        if types == DISK:
            return self.config_info.get(DISK)
        if device_name:
            for device in self.config_info.get(types).values():
                if device.get(DEVICE) == device_name:
                    return device
        return None

    def _run_test(self, testcase, config_data, subtests_filter=None):
        """
        Start a testing item
        :param testcase:
        :param subtests_filter:
        :return:
        """
        name = testcase[NAME]
        if testcase[DEVICE].get_name():
            name = testcase[NAME] + "-" + testcase[DEVICE].get_name()
        logname = name + ".log"
        reboot = None
        test = None
        logger = Logger(logname, self.job_id, sys.stdout, sys.stderr)
        logger.start()
        try:
            test = testcase[TEST]
            if subtests_filter:
                return_code = getattr(test, subtests_filter)()
            else:
                self.current_num += 1
                self.logger.info("Start to run %s/%s test suite: %s." %
                                 (self.current_num, self.total_count, name))
                args = argparse.Namespace(device=testcase[DEVICE], config_data=config_data, test_logger=logger,
                                          logdir=logger.logdir, testname=name)
                test.setup(args)
                if test.reboot:
                    reboot = Reboot(testcase[NAME], self, test.rebootup)
                    return_code = False
                    if reboot.setup():
                        return_code = test.test()
                else:
                    return_code = test.test()
        except Exception as concrete_error:
            logger.error("Failed to run %s. %s" % (name, concrete_error))
            return_code = False

        if reboot:
            reboot.clean()
        if not subtests_filter:
            test.teardown()
        logger.stop()
        self.logger.info("End to run %s/%s test suite: %s." %
                         (self.current_num, self.total_count, name))
        return return_code
