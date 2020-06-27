#!/usr/bin/env python
# coding: utf-8

# Copyright (c) 2020 Huawei Technologies Co., Ltd.
# oec-hardware is licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Create: 2020-04-01

from random import randint
from time import sleep

from hwcompatible.env import CertEnv
from hwcompatible.test import Test
from hwcompatible.command import Command, CertCommandError


class CPU(object):
    def __init__(self):
        self.cpu = None
        self.nums = None
        self.list = None
        self.numa_nodes = None
        self.governors = None
        self.original_governor = None
        self.max_freq = None
        self.min_freq = None

    def get_info(self):
        """
        Get CPU info
        :return:
        """
        cmd = Command("lscpu")
        try:
            nums = cmd.get_str(r'^CPU\S*:\s+(?P<cpus>\d+)$', 'cpus', False)
        except CertCommandError as e:
            print(e)
            return False
        self.nums = int(nums)
        self.list = range(self.nums)

        cmd = Command("cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq")
        try:
            max_freq = cmd.get_str()
        except CertCommandError as e:
            print(e)
            return False
        self.max_freq = int(max_freq)

        cmd = Command("cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_min_freq")
        try:
            min_freq = cmd.get_str()
        except CertCommandError as e:
            print(e)
            return False
        self.min_freq = int(min_freq)

        return True

    @staticmethod
    def set_freq(freq, cpu='all'):
        """
        Set CPU frequency
        :param freq:
        :param cpu:
        :return:
        """
        cmd = Command("cpupower -c %s frequency-set --freq %s" % (cpu, freq))
        try:
            cmd.run()
            return cmd.returncode
        except CertCommandError as e:
            print(e)
            return False

    @staticmethod
    def get_freq(cpu):
        """
        Get CPU frequency
        :param cpu:
        :return:
        """
        cmd = Command("cpupower -c %s frequency-info -w" % cpu)
        try:
            return int(cmd.get_str(r'.* frequency: (?P<freq>\d+) .*', 'freq', False))
        except CertCommandError as e:
            print(e)
            return False

    @staticmethod
    def set_governor(governor, cpu='all'):
        """
        Set the frequency governor mode of CPU
        :param governor:
        :param cpu:
        :return:
        """
        cmd = Command("cpupower -c %s frequency-set --governor %s" % (cpu, governor))
        try:
            cmd.run()
            return cmd.returncode
        except CertCommandError as e:
            print(e)
            return False

    @staticmethod
    def get_governor(cpu):
        """
        Get cpu governor
        :param cpu:
        :return:
        """
        cmd = Command("cpupower -c %s frequency-info -p" % cpu)
        try:
            return cmd.get_str(r'.* governor "(?P<governor>\w+)".*', 'governor', False)
        except CertCommandError as e:
            print(e)
            return False

    @staticmethod
    def find_path(parent_dir, target_name):
        """
        Find the target path from the specified directory
        :param parent_dir:
        :param target_name:
        :return:
        """
        cmd = Command("find %s -name %s" % (parent_dir, target_name))
        try:
            cmd.run()
            return cmd.returncode
        except CertCommandError as e:
            print(e)
            return False


class Load:
    """
    Let a program run on a specific CPU
    """
    def __init__(self, cpu):
        self.cpu = cpu
        self.process = Command("taskset -c {} python -u {}/cpufreq/cal.py".format(self.cpu, CertEnv.testdirectoy))
        self.returncode = None

    def run(self):
        """
        Process started
        :return:
        """
        self.process.start()  # background

    def get_runtime(self):
        """
        Get the running time of the process
        :return:
        """
        if not self.process:
            return None

        while self.returncode is None:
            self.returncode = self.process.poll()
        if self.returncode == 0:
            line = self.process.readline()
            return float(line)
        else:
            return False


class CPUFreqTest(Test):
    """
    CPU frequency test
    """
    def __init__(self):
        Test.__init__(self)
        self.requirements = ['util-linux', 'kernel-tools']
        self.cpu = CPU()
        self.original_governor = self.cpu.get_governor(0)

    def test_userspace(self):
        """
        userspace mode of testing CPU frequency
        :return:
        """
        target_cpu = randint(0, self.cpu.nums-1)
        target_freq = randint(self.cpu.min_freq, self.cpu.max_freq)
        if self.cpu.set_freq(target_freq, cpu=target_cpu) != 0:
            print("[X] Set CPU%s to freq %d failed." % (target_cpu, target_freq))
            return False
        print("[.] Set CPU%s to freq %d." % (target_cpu, target_freq))
        target_cpu_freq = self.cpu.get_freq(target_cpu)
        print("[.] Current freq of CPU%s is %d." % (target_cpu, target_cpu_freq))

        target_cpu_governor = self.cpu.get_governor(target_cpu)
        if target_cpu_governor != 'userspace':
            print("[X] The governor of CPU%s(%s) is not userspace." %
                  (target_cpu, target_cpu_governor))
            return False
        print("[.] The governor of CPU%s is %s." %
              (target_cpu, target_cpu_governor))

        # min_freq -> max_runtime
        self.cpu.set_freq(self.cpu.min_freq)
        load_list = []
        runtime_list = []
        for cpu in self.cpu.list:
            load_test = Load(cpu)
            load_test.run()
            load_list.append(load_test)
        for cpu in self.cpu.list:
            runtime = load_list[cpu].get_runtime()
            runtime_list.append(runtime)
        max_average_runtime = 1.0 * sum(runtime_list) / len(runtime_list)
        if max_average_runtime == 0:
            print("[X] Max average time is 0.")
            return False
        print("[.] Max average time of all CPUs userspace load test: %.2f" %
              max_average_runtime)

        # max_freq -> min_runtime
        self.cpu.set_freq(self.cpu.max_freq)
        load_list = []
        runtime_list = []
        for cpu in self.cpu.list:
            load_test = Load(cpu)
            load_test.run()
            load_list.append(load_test)
        for cpu in self.cpu.list:
            runtime = load_list[cpu].get_runtime()
            runtime_list.append(runtime)
        min_average_runtime = 1.0 * sum(runtime_list) / len(runtime_list)
        if min_average_runtime == 0:
            print("[X] Min average time is 0.")
            return False
        print("[.] Min average time of all CPUs userspace load test: %.2f" %
              min_average_runtime)

        measured_speedup = 1.0 * max_average_runtime / min_average_runtime
        expected_speedup = 1.0 * self.cpu.max_freq / self.cpu.min_freq
        tolerance = 1.0
        min_speedup = expected_speedup - (expected_speedup - 1.0) * tolerance
        max_speedup = expected_speedup + (expected_speedup - 1.0) * tolerance
        if not min_speedup < measured_speedup < max_speedup:
            print("[X] The speedup(%.2f) is not between %.2f and %.2f" %
                  (measured_speedup, min_speedup, max_speedup))
            return False
        print("[.] The speedup(%.2f) is between %.2f and %.2f" %
              (measured_speedup, min_speedup, max_speedup))

        return True

    def test_ondemand(self):
        """
        ondemand mode of testing CPU frequency
        :return:
        """
        if self.cpu.set_governor('powersave') != 0:
            print("[X] Set governor of all CPUs to powersave failed.")
            return False
        print("[.] Set governor of all CPUs to powersave.")

        if self.cpu.set_governor('ondemand') != 0:
            print("[X] Set governor of all CPUs to ondemand failed.")
            return False
        print("[.] Set governor of all CPUs to ondemand.")

        target_cpu = randint(0, self.cpu.nums)
        target_cpu_governor = self.cpu.get_governor(target_cpu)
        if target_cpu_governor != 'ondemand':
            print("[X] The governor of CPU%s(%s) is not ondemand." %
                  (target_cpu, target_cpu_governor))
            return False
        print("[.] The governor of CPU%s is %s." %
              (target_cpu, target_cpu_governor))

        load_test = Load(target_cpu)
        load_test.run()
        sleep(1)
        target_cpu_freq = self.cpu.get_freq(target_cpu)
        if target_cpu_freq != self.cpu.max_freq:
            print("[X] The freq of CPU%s(%d) is not scaling_max_freq(%d)." %
                  (target_cpu, target_cpu_freq, self.cpu.max_freq))
            return False
        print("[.] The freq of CPU%s is scaling_max_freq(%d)." %
              (target_cpu, target_cpu_freq))

        load_test_time = load_test.get_runtime()
        print("[.] Time of CPU%s ondemand load test: %.2f" %
              (target_cpu, load_test_time))
        target_cpu_freq = self.cpu.get_freq(target_cpu)
        if not target_cpu_freq <= self.cpu.max_freq:
            print("[X] The freq of CPU%s(%d) is not less equal than %d." %
                  (target_cpu, target_cpu_freq, self.cpu.max_freq))
            return False
        print("[.] The freq of CPU%s(%d) is less equal than %d." %
              (target_cpu, target_cpu_freq, self.cpu.max_freq))

        return True

    def test_conservative(self):
        """
        conservative mode of testing CPU frequency
        :return:
        """
        if self.cpu.set_governor('powersave') != 0:
            print("[X] Set governor of all CPUs to powersave failed.")
            return False
        print("[.] Set governor of all CPUs to powersave.")

        if self.cpu.set_governor('conservative') != 0:
            print("[X] Set governor of all CPUs to conservative failed.")
            return False
        print("[.] Set governor of all CPUs to conservative.")

        target_cpu = randint(0, self.cpu.nums)
        target_cpu_governor = self.cpu.get_governor(target_cpu)
        if target_cpu_governor != 'conservative':
            print("[X] The governor of CPU%s(%s) is not conservative." %
                  (target_cpu, target_cpu_governor))
            return False
        print("[.] The governor of CPU%s is %s." %
              (target_cpu, target_cpu_governor))

        load_test = Load(target_cpu)
        load_test.run()
        sleep(1)
        target_cpu_freq = self.cpu.get_freq(target_cpu)
        if not self.cpu.min_freq < target_cpu_freq < self.cpu.max_freq:
            print("[X] The freq of CPU%s(%d) is not between %d~%d." %
                  (target_cpu, target_cpu_freq, self.cpu.min_freq, self.cpu.max_freq))
            return False
        print("[.] The freq of CPU%s(%d) is between %d~%d." %
              (target_cpu, target_cpu_freq, self.cpu.min_freq, self.cpu.max_freq))

        load_test_time = load_test.get_runtime()
        print("[.] Time of CPU%s conservative load test: %.2f" %
              (target_cpu, load_test_time))
        target_cpu_freq = self.cpu.get_freq(target_cpu)
        print("[.] Current freq of CPU%s is %d." % (target_cpu, target_cpu_freq))

        return True

    def test_powersave(self):
        """
        powersave mode of testing CPU frequency
        :return:
        """
        if self.cpu.set_governor('powersave') != 0:
            print("[X] Set governor of all CPUs to powersave failed.")
            return False
        print("[.] Set governor of all CPUs to powersave.")

        target_cpu = randint(0, self.cpu.nums)
        target_cpu_governor = self.cpu.get_governor(target_cpu)
        if target_cpu_governor != 'powersave':
            print("[X] The governor of CPU%s(%s) is not powersave." %
                  (target_cpu, target_cpu_governor))
            return False
        print("[.] The governor of CPU%s is %s." %
              (target_cpu, target_cpu_governor))

        target_cpu_freq = self.cpu.get_freq(target_cpu)
        if target_cpu_freq != self.cpu.min_freq:
            print("[X] The freq of CPU%s(%d) is not scaling_min_freq(%d)." %
                  (target_cpu, target_cpu_freq, self.cpu.min_freq))
            return False
        print("[.] The freq of CPU%s is %d." % (target_cpu, target_cpu_freq))

        load_test = Load(target_cpu)
        load_test.run()
        load_test_time = load_test.get_runtime()
        print("[.] Time of CPU%s powersave load test: %.2f" %
              (target_cpu, load_test_time))
        target_cpu_freq = self.cpu.get_freq(target_cpu)
        print("[.] Current freq of CPU%s is %d." % (target_cpu, target_cpu_freq))

        return True

    def test_performance(self):
        """
        Performance mode of testing CPU frequency
        :return:
        """
        if self.cpu.set_governor('performance') != 0:
            print("[X] Set governor of all CPUs to performance failed.")
            return False
        print("[.] Set governor of all CPUs to performance.")

        target_cpu = randint(0, self.cpu.nums)
        target_cpu_governor = self.cpu.get_governor(target_cpu)
        if target_cpu_governor != 'performance':
            print("[X] The governor of CPU%s(%s) is not performance." %
                  (target_cpu, target_cpu_governor))
            return False
        print("[.] The governor of CPU%s is %s." %
              (target_cpu, target_cpu_governor))

        target_cpu_freq = self.cpu.get_freq(target_cpu)
        if target_cpu_freq != self.cpu.max_freq:
            print("[X] The freq of CPU%s(%d) is not scaling_max_freq(%d)." %
                  (target_cpu, target_cpu_freq, self.cpu.max_freq))
            return False
        print("[.] The freq of CPU%s is %d." % (target_cpu, target_cpu_freq))

        load_test = Load(target_cpu)
        load_test.run()
        load_test_time = load_test.get_runtime()
        print("[.] Time of CPU%s performance load test: %.2f" %
              (target_cpu, load_test_time))
        target_cpu_freq = self.cpu.get_freq(target_cpu)
        print("[.] Current freq of CPU%s is %d." % (target_cpu, target_cpu_freq))

        return True

    def test(self):
        """
        Test case
        :return:
        """
        if not self.cpu.get_info():
            print("[X] Fail to get CPU info."
                  " Please check if the CPU supports cpufreq.")
            return False

        ret = True
        print("")
        print("[.] Test userspace")
        if not self.test_userspace():
            print("[X] Test userspace FAILED")
            ret = False
        print("")
        print("[.] Test ondemand")
        if not self.test_ondemand():
            print("[X] Test ondemand FAILED")
            ret = False
        print("")
        print("[.] Test conservative")
        if not self.test_conservative():
            print("[X] Test conservative FAILED")
            ret = False
        print("")
        print("[.] Test powersave")
        if not self.test_powersave():
            print("[X] Test powersave FAILED")
            ret = False
        print("")
        print("[.] Test performance")
        if not self.test_performance():
            print("[X] Test performance FAILED")
            ret = False

        self.cpu.set_governor(self.original_governor)
        return ret


if __name__ == "__main__":
    t = CPUFreqTest()
    t.setup()
    t.test()
