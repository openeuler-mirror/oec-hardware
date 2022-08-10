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
# Create: 2022-03-01

import os
import stat

YES = "y"
SAMEASYES = ("y", "yes")
NO = "n"
SAMEASNO = ("n", "no")
TEST = "test"
PASS = "PASS"
FAIL = "FAIL"
FORCE = "Force"
RUN = "run"
NOTRUN = "NotRun"

OS = "OS"
KERNEL = "kernel"
OECH_VERSION = "oech_version"
OECH_NAME = "oech_name"
ID = "ID"
PRODUCTURL = "Product URL"
SERVER = "server"
NAME = "name"
CLASS = "Class"
DEVICE = "device"
BOARD = "boardModel"
CHIP = "chipModel"
DRIVER = "driverName"
VERSION = "driverVersion"
STATUS = "status"
REBOOT = "reboot"
SYSTEM = "system"

NODEVICE = ("cpufreq", "memory", "clock", "profiler", "system",
            "stress", "kdump", "perf", "acpi", "watchdog", "kabi")
CDTYPES = ("DVD_RW", "DVD_PLUS_RW", "DVD_R", "DVD_PLUS_R", "DVD",
           "BD_RE", "BD_R", "BD", "CD_RW", "CD_R", "CD")
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
FC = "fc"
RAID = "raid"
GPU = "gpu"
VGPU = "vgpu"
NVME = "nvme"
DPDK = "dpdk"
GPU_DRIVER = ("nouveau", "nvidia", "bi_driver", "amdgpu")
KEYCARD = "keycard"
KEYCARD_VENDORS = ('Xilinx', 'Renesas', 'Texas', 'PLX')
IB = "infiniband"
DEVICE_INFO = ('color', 'status', 'num', 'run', 'name',
               'device', 'driver', 'version', 'chip', 'board')

# File access control
FILE_FLAGS = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
FILE_MODES = stat.S_IWUSR | stat.S_IRUSR

# Shell command execute env
SHELL_ENV = {
    'LANG': 'en_US.UTF-8',
    'PATH': '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/root/bin'
}

# Log rotate settings
MAX_BYTES = 31457280
MAX_COUNT = 30