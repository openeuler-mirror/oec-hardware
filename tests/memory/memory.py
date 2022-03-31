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

"""memory test"""

import os
import time
import re
from hwcompatible.test import Test
from hwcompatible.command import Command, CertCommandError


class MemoryTest(Test):
    """
    Memory Test
    """

    def __init__(self):
        Test.__init__(self)
        self.requirements = ["libhugetlbfs-utils"]
        self.free_memory = 0
        self.system_memory = 0
        self.swap_memory = 0
        self.huge_pages = 1000
        self.hugepage_size = 0
        self.hugepage_total = 0
        self.hugepage_free = 0
        self.retry_list = list()
        self.logpath = None
        self.test_dir = os.path.dirname(os.path.realpath(__file__))

    def setup(self, args=None):
        """
        Initialization before test
        :return:
        """
        self.args = args or argparse.Namespace()
        self.logpath = getattr(args, "logdir", None) + "/memory.log"
        self.get_memory()

    def test(self):
        """
        test case
        :return:
        """
        if not self.memory_rw():
            return False

        if not self.eat_memory():
            return False

        if not self.hugetlb_test():
            return False

        if not self.memory_hotplug():
            return False

        return True

    def get_memory(self):
        """
        Get memory
        :return:
        """
        proc_meminfo = open("/proc/meminfo", "r")
        self.free_memory = 0
        self.system_memory = 0
        self.swap_memory = 0
        self.hugepage_size = 0
        self.hugepage_total = 0
        self.hugepage_free = 0
        while True:
            line = proc_meminfo.readline()
            if line:
                tokens = line.split()
                if len(tokens) == 3:
                    if tokens[0].strip() == "MemTotal:":
                        self.system_memory = int(tokens[1].strip())/1024
                    elif tokens[0].strip() in ["MemFree:", "Cached:", "Buffers:"]:
                        self.free_memory += int(tokens[1].strip())
                    elif tokens[0].strip() == "SwapTotal:":
                        self.swap_memory = int(tokens[1].strip())/1024
                    elif tokens[0].strip() == "Hugepagesize:":
                        self.hugepage_size = int(tokens[1].strip())/1024
                elif len(tokens) == 2:
                    if tokens[0].strip() == "HugePages_Total:":
                        self.hugepage_total = int(tokens[1].strip())
                    elif tokens[0].strip() == "HugePages_Free:":
                        self.hugepage_free = int(tokens[1].strip())
            else:
                break
        proc_meminfo.close()
        self.free_memory = self.free_memory/1024

    def memory_rw(self):
        """
        Test memory request
        :return:
        """
        if not self.system_memory:
            print("Error: get system memory fail.")
            return False

        test_mem = self.free_memory*90/100
        if test_mem > 1024*4:
            test_mem = 1024*4
        
        if os.system("memtester %sM 1" % test_mem) != 0:
            print("Error: memtester fail.")
            return False

        return True

    def eat_memory(self):
        """
        Eat memory test
        :return:
        """
        print("\nEat memory testing...")
        print("System Memory: %u MB" % self.system_memory)
        print("Free Memory: %u MB" % self.free_memory)
        print("Swap Memory: %u MB\n" % self.swap_memory)
        if not self.system_memory:
            print("Error: get system memory fail.")
            return False
        if self.swap_memory < 512:
            print("Error: swap memory of %s MB is too small." %
                  self.swap_memory)
            return False

        extra_mem = self.free_memory/100
        if extra_mem > self.swap_memory/2:
            extra_mem = self.swap_memory/2
        if extra_mem > 512:
            extra_mem = 512
        test_mem = extra_mem + self.free_memory
        if os.system("cd %s; ./eatmem_test -m %sM" % (self.test_dir, test_mem)) != 0:
            print("Error: eatmem_test failed, please check the space of SWAP.")
            return False

        return True

    def hugetlb_test(self):
        """
        hugetlb test
        :return:
        """
        print("\nHugetlb testing...")
        self.get_memory()
        print("HugePages Total: %u" % self.hugepage_total)
        print("HugePages Free: %u" % self.hugepage_free)
        print("HugePages Size: %uMB" % self.hugepage_size)
        update_hugepage = 1
        if self.hugepage_size >= 512:
            self.huge_pages = 10
        if not self.hugepage_total:
            os.system("hugeadm --create-mounts &>> %s" % self.logpath)
            os.system("hugeadm --pool-pages-min %dMB:%d &>> %s" %
                      (self.hugepage_size, self.huge_pages, self.logpath))
        elif self.hugepage_free < self.huge_pages:
            os.system("hugeadm --pool-pages-min %dMB:%d &>> %s" %
                      (self.hugepage_size, self.hugepage_total + self.huge_pages, self.logpath))
        else:
            update_hugepage = 0

        self.get_memory()
        if update_hugepage == 1:
            print("Updated hugepages:")
            print("HugePages Total: %u" % self.hugepage_total)
            print("HugePages Free: %u" % self.hugepage_free)
            print("HugePages Size: %uMB" % self.hugepage_size)

        if self.hugepage_free < self.huge_pages/2:
            print("Error: hugepages reserve fail.")
            return False

        try:
            Command("cd %s; ./hugetlb_test &>> %s" %
                    (self.test_dir, self.logpath)).echo()
            print("Hugetlb test succ.\n")
        except CertCommandError as concrete_error:
            print("Error: hugepages test fail.\n", concrete_error)
            return False
        return True

    def hot_plug_verify(self):
        """
        Verify hot plug
        :return:
        """
        kernel = Command("uname -r").read()
        config_file = "/boot/config-" + kernel
        if not os.path.exists(config_file):
            print("Config %s does not exist." % config_file)
            return False
        if os.system("grep -q -w 'CONFIG_MEMORY_HOTPLUG=y' %s" % config_file) != 0:
            print("Memory hotplug is not supported.")
            return False
        return True

    def hotplug_memory_test(self, memory_path):
        """
        Hotplug memory test
        :param memory_path:
        :return:
        """
        os.system("echo 'Keep %s online before test.' &>> %s"% (memory_path, self.logpath))
        if not self.online_memory(memory_path):
            return False

        os.system("echo 'Try to offline...' &>> %s"%self.logpath)
        self.get_memory()
        total_mem_1 = self.system_memory
        if not self.offline_memory(memory_path):
            return False

        self.get_memory()
        total_mem_2 = self.system_memory
        if total_mem_2 >= total_mem_1:
            return False

        os.system("echo 'Try to online...' &>> %s"%self.logpath)
        if not self.online_memory(memory_path):
            self.retry_list.append(memory_path)
            return False
        self.get_memory()
        total_mem_3 = self.system_memory
        if total_mem_3 != total_mem_1:
            return False

        return True

    def online_memory(self, memory_path):
        """
        Set memory online
        :param memory_path:
        :return:
        """
        try:
            Command("echo 1 > %s/online" % memory_path).run()
            Command("cat %s/state" % memory_path).get_str("online")
            return True
        except Exception:
            print("Error: fail to online %s." % memory_path)
            return False

    def offline_memory(self, memory_path):
        """
        Set memory offline
        :param memory_path:
        :return:
        """
        try:
            Command("echo 0 > %s/online" % memory_path).run()
            Command("cat %s/state" % memory_path).get_str("offline")
            return True
        except Exception:
            print("Error: fail to online %s." % memory_path)
            return False

    def memory_hotplug(self):
        """
        Memory hotplug test
        :return:
        """
        print("\nMemory hotplug testing...")
        if not self.hot_plug_verify():
            print("Warning: memory hotplug test skipped.")
            return True

        print("Searching removable memory...")
        if not os.path.exists("/sys/devices/system/node/"):
            return False

        return_code = True
        mem_path_list = list()
        pattern = re.compile("^memory[0-9]*$")
        for (dirpath, dirs, filenames) in os.walk("/sys/devices/system/node/"):
            mem_dirs = filter(pattern.search, dirs)
            for mem_dirname in mem_dirs:
                mem_path_list.append(os.path.join(dirpath, mem_dirname))

        if not mem_path_list:
            print("Error: no memory found.")
            return False

        test_flag = 0
        for memory_path in mem_path_list:
            try:
                Command("cat %s/removable" % memory_path).get_str("1")
                print("%s is removable, start testing..." %
                      os.path.basename(memory_path))
                test_flag = 1
            except:
                continue
            if not self.hotplug_memory_test(memory_path):
                print("%s hotplug test fail." % os.path.basename(memory_path))
                return_code = False

        if test_flag == 0:
            print("No removable memory found.")

        if self.retry_list:
            print("Retry to online memory after 2mins.")
            time.sleep(120)
            for memory_path in self.retry_list:
                self.online_memory(memory_path)

        return return_code


if __name__ == "__main__":
    main = MemoryTest()
    main.setup()
    main.test()
