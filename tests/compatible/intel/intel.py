#!/usr/bin/env python3
# coding: utf-8
# SPDX-License-Identifier: GPL-2.0-only
# Copyright (c) 2024 Intel Corporation
# @Author   yi.sun@intel.com

import os
import argparse
from hwcompatible.test import Test
from hwcompatible.command import Command

intel_dir = os.path.dirname(os.path.realpath(__file__))


class IntelTest(Test):
    def __init__(self):
        Test.__init__(self)
        self.requirements = [
            "gcc-c++", "make", "git", "automake", "make", "gcc", "m4", "libtool", "asciidoc",
            "xmlto", "uuid", "uuid-devel", "uuid-c++-devel", "libuuid-devel", "json-c-devel",
            "zlib-devel", "openssl-devel"]

        self.device = None

        self.tests = [
            ["amx/tmul", "tests-amx"],
            ["avx512vbmi", "tests-avx512vbmi"],
            ["cstate", "tests-cstate"],
            ["dsa", "tests-dsa1"],
            ["dsa", "tests-iax"],
            ["ifs", "tests-ifs"],
            ["pmu", "tests-pmu"],
            ["pstate", "tests-pstate"],
            ["rapl", "tests-rapl"],
            ["telemetry", "tests-telemetry"],
            ["topology", "tests-topology"],
            ["umip", "tests-umip"],
            ["xsave", "tests-xsave"]]

    def setup(self, args=None):
        self.args = args or argparse.Namespace()
        self.logger = getattr(args, "test_logger", None)
        self.device = getattr(args, 'device', None)
        self.command = Command(self.logger)

        os.chdir(intel_dir)
        ret = self.command.run_cmd("bash setup.sh")

        for t in self.tests:
            os.chdir(f'{intel_dir}/lkvs/BM/{t[0]}')
            if os.path.isfile("Makefile") and os.path.isfile("makefile"):
                result = self.command.run_cmd("make")

    def test(self):
        ret = 0
        os.chdir(f'{intel_dir}/lkvs/BM')

        for t in self.tests:
            result = self.command.run_cmd("python3 runtests.py -f %s -t %s/lkvs/scenario/emr-oe/%s"
                                          % (t[0], intel_dir, t[1]))
            if result[2] == 0:
                self.logger.info("%s: %s test successfully!" % (t[0], t[1]))
            else:
                self.logger.info("%s: %s test failed!" % (t[0], t[1]))
                ret += 1

        if (ret != 0):
            return False

        return True
