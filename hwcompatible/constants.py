# -*- encoding=utf-8 -*-
"""
# **********************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2021-2021. All rights reserved.
# [oecp] is licensed under the Mulan PSL v1.
# You can use this software according to the terms and conditions of the Mulan PSL v1.
# You may obtain a copy of Mulan PSL v1 at:
#     http://license.coscl.org.cn/MulanPSL
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v1 for more details.
# Author: meitingli
# Create: 2021-03-01
# Description: save constants objects
# **********************************************************************************
"""

TOTAL_COUNT = 0
CURRENT_NUM = 0
YES = "y"
SAMEASYES = ["y", "yes"]
NO = "n"
SAMEASNO = ["n", "no"]
TEST = "test"
PASS = "PASS"
FAIL = "FAIL"
FORCE = "Force"
RUN = "run"
NOTRUN = "NotRun"

OS = "OS"
KERNEL = "kernel"
ID = "ID"
PRODUCTURL = "Product URL"
SERVER = "server"
NAME = "name"
DEVICE = "device"
STATUS = "status"
REBOOT = "reboot"
SYSTEM = "system"

NODEVICE = ["cpufreq", "memory", "clock", "profiler", "system",
            "stress", "kdump", "perf", "acpi", "watchdog", "kabi"]
CDTYPES = ["DVD_RW", "DVD_PLUS_RW", "DVD_R", "DVD_PLUS_R", "DVD",
           "BD_RE", "BD_R", "BD", "CD_RW", "CD_R", "CD"]
SUBSYSTEM = "SUBSYSTEM"
PCI_CLASS = "PCI_CLASS"
USB = "usb"
VIDEO = "video"
DISK = "disk"
NVME = "nvme"
ETHERNET = "ethernet"
WIFI = "wifi"
WLAN = "wlan"
CDROM = "cdrom"
IPMI = "ipmi"
FC = "fibrechannel"
RAID = "raid"
GPU = "gpu"
GPU_DRIVER = ["nouveau", "nvidia", "bi_driver", "amdgpu"]
KEYCARD = "keycard"
KEYCARD_VENDORS = ['Xilinx', 'Renesas', 'Texas', 'PLX']
IB = "infiniband"
