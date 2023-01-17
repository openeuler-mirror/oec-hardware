#!/usr/bin/env python3
# coding: utf-8

# oec-hardware is licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Author: @ylzhangah
# Create: 2022-12-01
# Desc: DPDK test


import os
import glob
from math import log2


class ShowHugepages:
    """
     Format memsize, get moutpoint, show hugepages
    """

    def __init__(self, logger, command):
        self.logger = logger
        self.command = command

    def format_memsize(self, kb):
        """"
        format memsize. this is a code snippit from dpdk repo
        """
        binary_prefix = "KMG"
        logk = int(log2(kb) / 10)
        suffix = binary_prefix[logk]
        unit = 2 ** (logk * 10)
        if unit != 0:
            return '{}{}b'.format(int(kb / unit), suffix)
        else:
            return False

    def get_mountpoints(self):
        """
        Get list of where hugepage filesystem is mounted
        """
        mounted = self.command.run_cmd("mount | grep hugetlbfs | awk '{print $2}'")[0].strip('\n')
        return mounted

    def is_numa(self):
        """
        Test if numa is used on this system
        """
        return os.path.exists('/sys/devices/system/node')

    def show_numa_pages(self):
        """
        Show huge page reservations on numa system
        """
        self.logger.info('Node Pages Size Total')
        for numa_path in glob.glob('/sys/devices/system/node/node*'):
            node = numa_path[29:]  # slice after /sys/devices/system/node/node
            path = os.path.join(numa_path, 'hugepages')
            for hdir in os.listdir(path):
                comm = self.command.run_cmd("cat %s/%s/nr_hugepages" % (path, hdir))
                pages = int(comm[0].strip('\n'))
                if pages > 0:
                    kb = int(hdir[10:-2])  # slice out of hugepages-NNNkB
                    self.logger.info('{:<4} {:<5} {:<6} {}'.format(node, pages,
                        self.format_memsize(kb), self.format_memsize(pages * kb)))

    def show_non_numa_pages(self):
        """
        Show huge page reservations on non numa system
        """
        self.logger.info('Pages Size Total')
        hugepagedir = '/sys/kernel/mm/hugepages/'
        for hdir in os.listdir(hugepagedir):
            comm = self.command.run_cmd("cat %s/%s/nr_hugepages" % (hugepagedir, hdir))
            pages = int(comm[0].strip('\n'))
            if pages > 0:
                kb = int(hdir[10:-2])

                self.logger.info('{:<5} {:<6} {}'.format(pages, self.format_memsize(kb),
                    self.format_memsize(pages * kb)))

    def check_hugepage_allocate(self, isnuma):
        if not isnuma:
            hugepagedir = '/sys/kernel/mm/hugepages/'
        else:
            numaid = 0
            hugepagedir = '/sys/devices/system/node/node%d/hugepages/' % numaid

        for (_, dirs, _) in os.walk(hugepagedir):
            for directory in dirs:
                comm = self.command.run_cmd("cat %s/%s/nr_hugepages" % (hugepagedir, directory))
                if comm[0] != 0:
                    return True
            break

        return False

        # return false when
        # 1. no files in hugepagedir;
        # 2. no non-zero entry was found;
