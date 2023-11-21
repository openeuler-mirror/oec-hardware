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
from .env import CertEnv
from .command import Command
from .log import Logger
from .reboot import Reboot
from .cert_info import CertInfo
from .constants import NO_CONFIG_DEVICES, NODEVICE
from .config_ip import ConfigIP


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
        self.config_info = {}
        self.logger = Logger("job.log", self.job_id, sys.stdout, sys.stderr)
        self.command = Command(self.logger)
        self.yaml_file = CertEnv.configfile
        self.total_count = 0
        self.current_num = 0
        self.config_flag = 0

    def check_test_depends(self):
        """
        Install  dependency packages
        :return: depending
        """
        required_rpms = []
        for tests in self.test_suite:
            for pkg in tests["test"].requirements:
                cmd_result = self.command.run_cmd(
                    "rpm -q %s" % pkg, ignore_errors=True, log_print=False)
                return_code = cmd_result[2]
                if return_code != 0 and pkg not in required_rpms:
                    required_rpms.append(pkg)

        if required_rpms:
            self.logger.info("Start to install required packages: %s" %
                             ", ".join(required_rpms))
            cmd_result = self.command.run_cmd(
                "yum install -y %s" % (" ".join(required_rpms)))
            if len(cmd_result[1]) != 0 and cmd_result[2] != 0:
                self.logger.error(
                    "Fail to install required packages.\n %s" % cmd_result[1])
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
        self.test_suite.sort(key=lambda k: k["test"].pri)
        cert_infos = CertInfo(self.logger, self.command)
        for testcase in self.test_suite:
            config_data = self.get_device(testcase)
            if self._run_test(testcase, config_data, subtests_filter):
                testcase["status"] = "PASS"
                self.logger.info("Test %s succeed." %
                                 testcase["name"], terminal_print=False)

                if testcase["name"] not in NODEVICE:
                    cert_infos.create_json(testcase["name"], testcase["device"])
            else:
                testcase["status"] = "FAIL"
                self.logger.error("Test %s failed." %
                                  testcase["name"], terminal_print=False)

        cert_infos.export_cert_info()

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
            if not test["run"]:
                continue
            name = test["name"]
            if test["device"].get_name():
                name = test["name"] + "-" + test["device"].get_name()
            if test["status"] == "PASS":
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
                if test["name"] == testcase["name"] and test["device"].path == \
                        testcase["device"].path:
                    test["status"] = testcase["status"]

    def get_config(self):
        """
        get configuration file
        """
        if not os.path.exists(self.yaml_file):
            self.logger.error("Failed to get configuration file information.")
            return False
        try:
            with open(self.yaml_file, 'r', encoding="utf-8") as file:
                file_data = file.read()
                self.config_info = yaml.safe_load(file_data)
        except yaml.scanner.ScannerError:
            self.logger.error(
                "The yaml file %s format is error." % self.yaml_file)
            return False

        return True

    def get_device(self, testcase):
        """
        Get the board configuration information to be tested
        """
        types = testcase["name"]
        device_name = testcase["device"].get_name()
        self.config_flag = 0
        if types == "disk":
            self.config_flag = 1
            return self.config_info.get("disk", "all")
        if device_name and types not in NO_CONFIG_DEVICES:
            for device in self.config_info.get(types).values():
                if device.get("device") == device_name:
                    self.config_flag = 1
                    return device
        return None

    def _run_test(self, testcase, config_data, subtests_filter=None):
        """
        Start a testing item
        :param testcase:
        :param subtests_filter:
        :return:
        """
        name = testcase["name"]
        device_name = testcase["device"].get_name()
        if device_name:
            name = testcase["name"] + "-" + device_name
        logname = name + ".log"
        reboot = None
        test = None
        logger = Logger(logname, self.job_id, sys.stdout, sys.stderr)
        logger.start()
        try:
            test = testcase["test"]
            if subtests_filter and name != "system":
                return_code = getattr(test, subtests_filter)(logger)
            else:
                self.current_num += 1
                self.logger.info("Start to run %s/%s test suite: %s." %
                                 (self.current_num, self.total_count, name))

                if device_name and self.config_flag == 0 and testcase["name"] not in NO_CONFIG_DEVICES:
                    self.logger.error("Failed to check configuration file!"
                            "\nPlease configure the board information in file '%s'." % self.yaml_file)
                    return False

                if testcase['name'] in ('ethernet', 'infiniband'):
                    auto_config_ip = ConfigIP(config_data, logger, testcase["device"])
                    if not auto_config_ip.config_ip():
                        self.logger.error("Config IP address failed.")
                        return False

                args = argparse.Namespace(
                    device=testcase["device"], config_data=config_data,
                    test_logger=logger, logdir=logger.logdir, testname=name)
                test.setup(args)
                if test.reboot:
                    reboot = Reboot(testcase["name"], self, test.rebootup)
                    return_code = False
                    if reboot.setup(args):
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
