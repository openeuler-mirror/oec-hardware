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
# Author: @meitingli
# Create: 2022-07-09
# Desc: Common functions

import os
import sys
import shutil
import filecmp
import importlib
from .test import Test
from .env import CertEnv
from .constants import NODEVICE, TEST_KABI_ARCH
from .command import Command


def create_test_suite(test_factory, logger, category="compatible", subtests_filter=None):
    """
    Create test suites for job testing
    Args:
        test_factory (list): total test factory
        logger (Logger): logger object to record
        category (str): test category
        subtests_filter (list, optional): filter object. Defaults to None.

    Returns:
        test_suite (list）: available test suites 
    """
    test_suite = []
    test_name = []
    kabi_select = 0
    kabi_test = None
    for test in test_factory:
        if test["run"]:
            testcase = __create_testcase(test, logger, subtests_filter)
            if testcase:
                test_suite.append(testcase)
                test_name.append(test["name"])

            if category == "compatible" and test["name"] not in NODEVICE:
                kabi_select = 1
            if "kabi" in test_name:
                kabi_select = 0
        if test["name"] == "kabi":
            kabi_test = test

    command = Command(logger)
    arch = command.run_cmd("uname -m")[0].strip()
    if kabi_select and arch in TEST_KABI_ARCH:
        logger.info("The hardware will test kabi automatically.")
        kabi_test["run"] = True
        testcase = __create_testcase(kabi_test, logger, subtests_filter)
        if testcase:
            test_suite.append(testcase)
            test_name.append("kabi")

    total_count = len(test_suite)
    if total_count:
        logger.info("There are %s selected test suites: %s." %
                    (total_count, ", ".join(test_name)))
    return test_suite


def __create_testcase(test, logger, subtests_filter):
    """
    Create testcase
    Args:
        test (dict): _description_
        logger (Logger): logger object to record
        subtests_filter (list, optional): filter object. Defaults to None.

    Returns:
        testcase (dict): available testcase or None 
    """
    testclass = discover(test["name"], logger, subtests_filter)
    if not testclass and not subtests_filter:
        test["status"] = "FAIL"
        logger.error("The testcase %s is not found." % test["name"])
        return False

    testcase = dict()
    testcase["test"] = testclass
    testcase["name"] = test["name"]
    testcase["device"] = test["device"]
    testcase["status"] = "FAIL"
    return testcase


def copy_pci():
    """
    copy the PCI file if it exists
    """
    if os.path.exists(CertEnv.pcifile) and \
            not filecmp.cmp(CertEnv.oechpcifile, CertEnv.pcifile):
        copyfile = CertEnv.pcifile + ".copy"
        shutil.move(CertEnv.pcifile, copyfile)
        shutil.copy(CertEnv.oechpcifile, CertEnv.pcifile)


def discover(testname, logger, subtests_filter=None):
    """
    discover test
    :param testname:
    :param subtests_filter:
    :return:
    """
    if not testname:
        logger.warning("Testname is not specified, discover test failed.")
        return False

    filename = testname + ".py"
    dirpath = ''
    for sublist in os.walk(CertEnv.testdirectoy):
        if filename in sublist[2]:
            dirpath = sublist[0]
            break
    pth = os.path.join(dirpath, filename)
    if not os.access(pth, os.R_OK):
        return False

    sys.path.insert(0, dirpath)
    module = importlib.import_module(testname)
    for thing in dir(module):
        test_class = getattr(module, thing)
        if isinstance(test_class, type) and issubclass(test_class, Test):
            if "test" not in dir(test_class):
                continue
            if (subtests_filter and subtests_filter not in dir(test_class)):
                continue
            test = test_class()
            if "pri" not in dir(test):
                continue
            return test

    return False


def recovery_pci():
    """
    recovery the system PCI file
    """
    copyfile = CertEnv.pcifile + ".copy"
    if os.path.exists(CertEnv.pcifile) and \
            os.path.exists(copyfile):
        os.remove(CertEnv.pcifile)
        shutil.move(copyfile, CertEnv.pcifile)


def search_factory(obj_test, test_factory):
    """
    Determine whether test exists by searching test_factory
    :param obj_test:
    :param test_factory:
    :return:
    """
    for test in test_factory:
        if test["name"] == obj_test["name"] and \
                test["device"].path == obj_test["device"].path:
            return True
    return False
