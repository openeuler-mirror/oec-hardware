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
# Desc: cpufreq test

import argparse
from random import randint
from time import sleep
from threading import Thread
from hwcompatible.env import CertEnv
from hwcompatible.test import Test
from hwcompatible.command import Command


class CPU:
    """
    cpufreq test
    """

    def __init__(self, logger, command):
        self.cpu = None
        self.nums = 0
        self.list = None
        self.original_governor = None
        self.max_freq = 0
        self.min_freq = 0
        self.logger = logger
        self.command = command

    def get_info(self):
        """
        Get CPU info
        :return:
        """
        cmd_result = self.command.run_cmd(
                "lscpu | grep '^CPU(s):' | awk '{print $2}'")
        self.logger.info("Get the CPU(s) succeed.")
        self.nums = int(cmd_result[0])
        self.list = range(self.nums)

        cmd = self.command.run_cmd(
            "cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq")
        if cmd[2] != 0:
            self.logger.error("Get the scaling_max_freq of cpu failed.")
            return False
        self.max_freq = int(cmd[0])

        cmd = self.command.run_cmd(
            "cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_min_freq")
        if cmd[2] != 0:
            self.logger.error("Get the scaling_min_freq of cpu failed.")
            return False
        self.min_freq = int(cmd[0])

        return True

    def set_freq(self, freq, cpu='all'):
        """
        Set CPU frequency
        :param freq:
        :param cpu:
        :return:
        """
        cmd = self.command.run_cmd(
            "cpupower -c %s frequency-set --freq %s" % (cpu, freq), log_print=False)
        return cmd[2] == 0

    def get_freq(self, cpu):
        """
        Get CPU frequency
        :param cpu:
        :return:
        """
        cmd = self.command.run_cmd(
                "cpupower -c %s frequency-info -w | grep 'frequency' | cut -d ' ' -f 6" % cpu)
        try:
            if int(cmd[0]) and cmd[2] == 0:
                self.logger.info("Get cpu frequency succeed.")
        except ValueError as e:
            self.logger.error("Get cpu frequency failed, %s" % e)
            self.logger.info("Please use 'cpupower frequency-info' to check current frequency manually.")
            return False
        return int(cmd[0])

    def set_governor(self, governor, cpu='all'):
        """
        Set the frequency governor mode of CPU
        :param governor:
        :param cpu:
        :return:
        """
        cmd = self.command.run_cmd(
            "cpupower -c %s frequency-set --governor %s" % (cpu, governor), log_print=False)
        return cmd[2] == 0

    def get_governor(self, cpu):
        """
        Get cpu governor
        :param cpu:
        :return:
        """
        cmd = self.command.run_cmd(
            "cpupower -c %s frequency-info -p | grep governor | cut -d '\"' -f 2" % cpu)
        if cmd[2] != 0:
            self.logger.error("Get cpu governor failed.")
            return False
        self.logger.info("Get cpu governor succeed.")
        return cmd[0].strip()


class Load(Thread):
    """
    Let a program run on a specific CPU
    """

    def __init__(self, cpu, command):
        Thread.__init__(self)
        self.cpu = cpu
        self.command = command
        self.process = None
        self.returncode = None

    def run(self):
        """
        Process started
        :return:
        """
        self.process = self.command.run_cmd(
            "taskset -c %s python -u %s/cpufreq/cal.py" % (self.cpu, CertEnv.testdirectoy), log_print=False)

    def get_runtime(self):
        """
        Get the running time of the process
        :return:
        """
        while self.is_alive():
            sleep(0.02)
            
        self.returncode = self.process[2]
        if self.returncode == 0:
            line = self.process[0]
            return float(line)
        return 0


class CPUFreqTest(Test):
    """
    CPU frequency test
    """

    def __init__(self):
        Test.__init__(self)
        self.requirements = ['util-linux', 'kernel-tools']
        self.cpu = None
        self.original_governor = None

    def setup(self, args=None):
        """
        Initialization before test
        :param args:
        :return:
        """
        self.args = args or argparse.Namespace()
        self.logger = getattr(self.args, "test_logger", None)
        self.command = Command(self.logger)
        self.cpu = CPU(self.logger, self.command)
        self.original_governor = self.cpu.get_governor(0)

    def test_userspace(self):
        """
        userspace mode of testing CPU frequency
        :return:
        """
        target_cpu = randint(0, self.cpu.nums-1)
        target_freq = randint(self.cpu.min_freq, self.cpu.max_freq)
        if not self.cpu.set_freq(target_freq, cpu=target_cpu):
            self.logger.error("Set CPU%s to freq %d failed." %
                              (target_cpu, target_freq))
            return False
        self.logger.info("Set CPU%s to freq %d." % (target_cpu, target_freq))
        target_cpu_freq = self.cpu.get_freq(target_cpu)
        self.logger.info("Current freq of CPU%s is %d." %
                         (target_cpu, target_cpu_freq))

        target_cpu_governor = self.cpu.get_governor(target_cpu)
        if target_cpu_governor != 'userspace':
            self.logger.error("The governor of CPU%s(%s) is not userspace." %
                              (target_cpu, target_cpu_governor))
            return False
        self.logger.info("The governor of CPU%s is %s." %
                         (target_cpu, target_cpu_governor))

        # min_freq -> max_runtime
        self.cpu.set_freq(self.cpu.min_freq)
        load_list = []
        runtime_list = []
        for cpu in self.cpu.list:
            load_test = Load(cpu, self.command)
            load_test.start()
            load_list.append(load_test)
        for cpu in self.cpu.list:
            runtime = load_list[cpu].get_runtime()
            runtime_list.append(runtime)
        max_average_runtime = 1.0 * sum(runtime_list) / len(runtime_list)
        if max_average_runtime == 0:
            self.logger.error("Max average time is 0.")
            return False
        self.logger.info(
            "Max average time of all CPUs userspace load test: %.2f" % max_average_runtime)

        # max_freq -> min_runtime
        self.cpu.set_freq(self.cpu.max_freq)
        load_list = []
        runtime_list = []
        for cpu in self.cpu.list:
            load_test = Load(cpu, self.command)
            load_test.start()
            load_list.append(load_test)
        for cpu in self.cpu.list:
            runtime = load_list[cpu].get_runtime()
            runtime_list.append(runtime)
        min_average_runtime = 1.0 * sum(runtime_list) / len(runtime_list)
        if min_average_runtime == 0:
            self.logger.info("Min average time is 0.")
            return False
        self.logger.info(
            "Min average time of all CPUs userspace load test: %.2f" % min_average_runtime)

        measured_speedup = 1.0 * max_average_runtime / min_average_runtime
        expected_speedup = 1.0 * self.cpu.max_freq / self.cpu.min_freq
        tolerance = 1.0
        min_speedup = expected_speedup - (expected_speedup - 1.0) * tolerance
        max_speedup = expected_speedup + (expected_speedup - 1.0) * tolerance
        if not min_speedup <= measured_speedup <= max_speedup:
            self.logger.error("The speedup(%.2f) is not between %.2f and %.2f" % (
                measured_speedup, min_speedup, max_speedup))
            return False
        self.logger.info("The speedup(%.2f) is between %.2f and %.2f" %
                         (measured_speedup, min_speedup, max_speedup))

        return True

    def test_ondemand(self):
        """
        ondemand mode of testing CPU frequency
        :return:
        """
        if not self.cpu.set_governor('powersave'):
            self.logger.error("Set governor of all CPUs to powersave failed.")
            return False
        self.logger.info("Set governor of all CPUs to powersave succeed.")

        if not self.cpu.set_governor('ondemand'):
            self.logger.error("Set governor of all CPUs to ondemand failed.")
            return False
        self.logger.info("Set governor of all CPUs to ondemand succeed.")

        target_cpu = randint(0, self.cpu.nums-1)
        target_cpu_governor = self.cpu.get_governor(target_cpu)
        if target_cpu_governor != 'ondemand':
            self.logger.error("The governor of CPU%s(%s) is not ondemand." % (
                target_cpu, target_cpu_governor))
            return False
        self.logger.info("The governor of CPU%s is %s." %
                         (target_cpu, target_cpu_governor))

        load_test = Load(target_cpu, self.command)
        load_test.start()
        sleep(1)
        target_cpu_freq = self.cpu.get_freq(target_cpu)
        if target_cpu_freq != self.cpu.max_freq:
            self.logger.error("The freq of CPU%s(%d) is not scaling_max_freq(%d)." % (
                target_cpu, target_cpu_freq, self.cpu.max_freq))
            return False
        self.logger.info("The freq of CPU%s is scaling_max_freq(%d)." %
                         (target_cpu, target_cpu_freq))

        load_test_time = load_test.get_runtime()
        self.logger.info("Time of CPU%s ondemand load test: %.2f" %
                         (target_cpu, load_test_time))
        target_cpu_freq = self.cpu.get_freq(target_cpu)
        if not target_cpu_freq <= self.cpu.max_freq:
            self.logger.error("The freq of CPU%s(%d) is not less equal than %d." % (
                target_cpu, target_cpu_freq, self.cpu.max_freq))
            return False
        self.logger.info("The freq of CPU%s(%d) is less equal than %d." % (
            target_cpu, target_cpu_freq, self.cpu.max_freq))

        return True

    def test_conservative(self):
        """
        conservative mode of testing CPU frequency
        :return:
        """
        if not self.cpu.set_governor('powersave'):
            self.logger.error("Set governor of all CPUs to powersave failed.")
            return False
        self.logger.info("Set governor of all CPUs to powersave.")

        if not self.cpu.set_governor('conservative'):
            self.logger.error(
                "Set governor of all CPUs to conservative failed.")
            return False
        self.logger.info("Set governor of all CPUs to conservative.")

        target_cpu = randint(0, self.cpu.nums-1)
        target_cpu_governor = self.cpu.get_governor(target_cpu)
        if target_cpu_governor != 'conservative':
            self.logger.error("The governor of CPU%s(%s) is not conservative." %
                              (target_cpu, target_cpu_governor))
            return False
        self.logger.info("The governor of CPU%s is %s." %
                         (target_cpu, target_cpu_governor))

        load_test = Load(target_cpu, self.command)
        load_test.start()
        sleep(1)
        target_cpu_freq = self.cpu.get_freq(target_cpu)
        if not self.cpu.min_freq <= target_cpu_freq <= self.cpu.max_freq:
            self.logger.error("The freq of CPU%s(%d) is not between %d~%d." %
                              (target_cpu, target_cpu_freq, self.cpu.min_freq, self.cpu.max_freq))
            return False
        self.logger.info("The freq of CPU%s(%d) is between %d~%d." %
                         (target_cpu, target_cpu_freq, self.cpu.min_freq, self.cpu.max_freq))

        load_test_time = load_test.get_runtime()
        self.logger.info("Time of CPU%s conservative load test: %.2f" %
                         (target_cpu, load_test_time))
        target_cpu_freq = self.cpu.get_freq(target_cpu)
        self.logger.info("Current freq of CPU%s is %d." %
                         (target_cpu, target_cpu_freq))

        return True

    def test_powersave(self):
        """
        Powersave mode of testing CPU frequency
        :return:
        """
        if not self.cpu.set_governor('powersave'):
            self.logger.error("Set governor of all CPUs to powersave failed.")
            return False
        self.logger.info("Set governor of all CPUs to powersave.")

        target_cpu = randint(0, self.cpu.nums-1)
        target_cpu_governor = self.cpu.get_governor(target_cpu)
        if target_cpu_governor != 'powersave':
            self.logger.error("The governor of CPU%s(%s) is not powersave." %
                              (target_cpu, target_cpu_governor))
            return False
        self.logger.info("The governor of CPU%s is %s." %
                         (target_cpu, target_cpu_governor))

        target_cpu_freq = self.cpu.get_freq(target_cpu)
        if target_cpu_freq != self.cpu.min_freq:
            self.logger.error("The freq of CPU%s(%d) is not scaling_min_freq(%d)." %
                              (target_cpu, target_cpu_freq, self.cpu.min_freq))
            return False
        self.logger.info("The freq of CPU%s is %d." %
                         (target_cpu, target_cpu_freq))

        load_test = Load(target_cpu, self.command)
        load_test.start()
        load_test_time = load_test.get_runtime()
        self.logger.info("Time of CPU%s powersave load test: %.2f" %
                         (target_cpu, load_test_time))
        target_cpu_freq = self.cpu.get_freq(target_cpu)
        self.logger.info("Current freq of CPU%s is %d." %
                         (target_cpu, target_cpu_freq))

        return True

    def test_performance(self):
        """
        Performance mode of testing CPU frequency
        :return:
        """
        if not self.cpu.set_governor('performance'):
            self.logger.error(
                "Set governor of all CPUs to performance failed.")
            return False
        self.logger.info("Set governor of all CPUs to performance.")

        target_cpu = randint(0, self.cpu.nums-1)
        target_cpu_governor = self.cpu.get_governor(target_cpu)
        if target_cpu_governor != 'performance':
            self.logger.error("The governor of CPU%s(%s) is not performance." %
                              (target_cpu, target_cpu_governor))
            return False
        self.logger.info("The governor of CPU%s is %s." %
                         (target_cpu, target_cpu_governor))

        target_cpu_freq = self.cpu.get_freq(target_cpu)
        if target_cpu_freq != self.cpu.max_freq:
            self.logger.error("The freq of CPU%s(%d) is not scaling_max_freq(%d)." %
                              (target_cpu, target_cpu_freq, self.cpu.max_freq))
            return False
        self.logger.info("The freq of CPU%s is %d." %
                         (target_cpu, target_cpu_freq))

        load_test = Load(target_cpu, self.command)
        load_test.start()
        load_test_time = load_test.get_runtime()
        self.logger.info("Time of CPU%s performance load test: %.2f" %
                         (target_cpu, load_test_time))
        target_cpu_freq = self.cpu.get_freq(target_cpu)
        self.logger.info("Current freq of CPU%s is %d." %
                         (target_cpu, target_cpu_freq))

        return True

    def test(self):
        """
        Test case
        :return:
        """
        if not self.cpu.get_info():
            self.logger.error(
                "Fail to get CPU info.\n Please check if the CPU supports cpufreq.")
            return False

        ret = True
        self.logger.info("Test userspace.")
        if not self.test_userspace():
            self.logger.error("Test userspace failed.")
            ret = False

        self.logger.info("Test ondemand.")
        if not self.test_ondemand():
            self.logger.error("Test ondemand failed.")
            ret = False

        self.logger.info("Test conservative.")
        if not self.test_conservative():
            self.logger.error("Test conservative failed.")
            ret = False

        self.logger.info("Test powersave.")
        if not self.test_powersave():
            self.logger.error("Test powersave failed.")
            ret = False

        self.logger.info("Test performance.")
        if not self.test_performance():
            self.logger.error("Test performance failed.")
            ret = False

        self.cpu.set_governor(self.original_governor)
        return ret
