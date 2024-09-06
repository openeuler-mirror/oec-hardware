#!/usr/bin/env python3
# coding: utf-8
# SPDX-License-Identifier: GPL-2.0-only
# Copyright (c) 2024 Intel Corporation
# @Author   yi.sun@intel.com

import os
import argparse
import subprocess
from hwcompatible.test import Test
from hwcompatible.command import Command

intel_dir = os.path.dirname(os.path.realpath(__file__))


class IntelTest(Test):
    # Mapping of CPU family IDs to platform names
    cpu_family_mapping = {
        '143': 'spr',
        '207': 'emr',
        '173': 'gnr',
    }

    def get_cpu_family_id(self):
        # Run the 'lscpu' command and capture its output
        result = subprocess.run(['/usr/bin/lscpu'], capture_output=True, text=True, check=True)

        # Split the output into lines
        output_lines = result.stdout.splitlines()

        # Find the line containing "Model:" and extract the family ID
        for line in output_lines:
            if "Model:" in line:
                # Assuming the family ID follows 'Model:' and is separated by spaces
                family_id = line.split(':')[1].strip()
                return family_id
                    # If "Model:" line is not found, raise an exception

        self.logger.info("[FAIL] 'Model:' not found in lscpu output")
        raise ValueError("'Model:' entry not found in lscpu output")

    def __init__(self):
        Test.__init__(self)
        self.requirements = [
            "gcc-c++", "make", "git", "automake", "gcc", "m4", "libtool", "asciidoc",
            "xmlto", "uuid", "uuid-devel", "uuid-c++-devel", "libuuid-devel", "json-c-devel",
            "zlib-devel", "openssl-devel", "perf", "stress-ng", "hwloc", "python3-pip",
            "pciutils-devel", "libcap-devel"]

        self.device = None
        self.env_check = {
            'stdout':'',
            'stderr':'',
            'ret':0}

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
        self.env_check['stdout'] = ret[0]
        self.env_check['stderr'] = ret[1]
        self.env_check['ret'] = ret[2]

        for t in self.tests:
            os.chdir(f'{intel_dir}/lkvs/BM/{t[0]}')
            if os.path.isfile("Makefile") or os.path.isfile("makefile"):
                result = self.command.run_cmd("make")

        if self.env_check['ret'] != 0:
            self.logger.info("[FAIL] Failed to setup environment!")
            return False

        return True

    def test(self):
        platform = self.cpu_family_mapping.get(self.get_cpu_family_id())

        if self.env_check['ret'] != 0:
            return False

        ret = 0
        os.chdir(f'{intel_dir}/lkvs/BM')

        for t in self.tests:
            if not os.path.isfile(f'{intel_dir}/lkvs/scenario/{platform}-oe/{t[1]}'):
                continue

            result = self.command.run_cmd("python3 runtests.py -f %s -t %s/lkvs/scenario/%s-oe/%s"
                                          % (t[0], intel_dir, platform, t[1]))
            if result[2] == 0:
                self.logger.info("[PASS]%s: %s test successfully!" % (t[0], t[1]))
            else:
                self.logger.info("[FAIL]%s: %s test failed!" % (t[0], t[1]))
                ret += 1

        if (ret != 0):
            return False

        return True
