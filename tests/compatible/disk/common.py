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
# Author: @cuixucui
# Create: 2022-09-23

import os
import shutil
from subprocess import getoutput
from hwcompatible.device import CertDevice


def query_disk(logger, command):
    """
    query disk info
    """
    logger.info("Disk Info:", terminal_print=False)
    command.run_cmd("fdisk -l")
    logger.info("Partition Info:", terminal_print=False)
    command.run_cmd("df -h")
    logger.info("Mount Info:", terminal_print=False)
    command.run_cmd("mount")
    logger.info("Swap Info:", terminal_print=False)
    command.run_cmd("cat /proc/swaps")
    logger.info("LVM Info:", terminal_print=False)
    command.run_cmd("pvdisplay")
    command.run_cmd("vgdisplay")
    command.run_cmd("lvdisplay")
    logger.info("Md Info:", terminal_print=False)
    command.run_cmd("cat /proc/mdstat")


def get_disk(logger, command, config_data, pci_num=""):
    """
    Get disk info
    """
    disks = list()
    test_disks = []
    devices = CertDevice(logger).get_devices()
    for device in devices:
        if (device.get_property("DEVTYPE") == "disk" and not device.get_property("ID_TYPE")) or\
                device.get_property("ID_TYPE") == "disk":
            if "/host" in device.get_property("DEVPATH"):
                if isinstance(config_data, str):
                    disks.append(device.get_name())
                elif pci_num in device.get_property("DEVPATH"):
                    disks.append(device.get_name())

    command.run_cmd("/usr/sbin/swapon -a")
    with open("/proc/partitions", "r") as partition_file:
        partition = partition_file.read()

    with open("/proc/swaps", "r") as swap_file:
        swap = swap_file.read()

    with open("/proc/mdstat", "r") as mdstat_file:
        mdstat = mdstat_file.read()

    with open("/proc/mounts", "r") as mount_file:
        mounts = mount_file.read()

    for disk in disks:
        if disk not in partition or ("/dev/%s" % disk) in swap:
            continue
        if ("/dev/%s" % disk) in mounts or disk in mdstat:
            continue
        result = command.run_cmd("pvs | grep -q '/dev/%s'" % disk)
        if result[2] == 0:
            continue
        test_disks.append(disk)

    un_suitable = list(set(disks).difference(set(test_disks)))
    if len(un_suitable) > 0:
        logger.info("These disks %s are in use now, skip them." % "|".join(un_suitable))
    return test_disks


def raw_test(logger, command, disk):
    """
    Raw test
    """
    logger.info("%s raw IO test" % disk)
    device = os.path.join("/dev", disk)
    if not os.path.exists(device):
        logger.error("Device %s doesn't exist." % device)
        return False
    proc_path = os.path.join("/sys/block/", disk)
    if not os.path.exists(proc_path):
        proc_path = os.path.join("/sys/block/*/", disk)
    size = getoutput("cat %s/size" % proc_path)
    size = int(size) / 2
    if size <= 0:
        logger.error(
            "Device %s size is not suitable for testing." % device)
        return False
    elif size > 1048576:
        size = 1048576

    logger.info("Starting sequential raw IO test...")
    opts = "-direct=1 -iodepth 4 -rw=rw -rwmixread=50 -group_reporting -name=file -runtime=300"
    if not do_fio(logger, command, device, size, opts):
        logger.error("%s sequential raw IO test failed." % device)
        return False

    logger.info("Starting rand raw IO test...")
    opts = "-direct=1 -iodepth 4 -rw=randrw -rwmixread=50 " \
           "-group_reporting -name=file -runtime=300"
    if not do_fio(logger, command, device, size, opts):
        logger.error("%s rand raw IO test failed." % device)
        return False

    return True


def vfs_test(logger, command, disk, filesystems):
    """
    Vfs test
    """
    logger.info("%s vfs test" % disk)
    device = os.path.join("/dev/", disk)
    if not os.path.exists(device):
        logger.error("Device %s doesn't exist." % device)
        return False
    proc_path = os.path.join("/sys/block/", disk)
    if not os.path.exists(proc_path):
        proc_path = os.path.join("/sys/block/*/", disk)
    size = getoutput("cat %s/size" % proc_path)
    size = int(size) / 2 / 2
    if size <= 0:
        logger.error(
            "Device %s size is not suitable for testing." % device)
        return False
    elif size > 1048576:
        size = 1048576

    if os.path.exists("vfs_test"):
        shutil.rmtree("vfs_test")
    os.mkdir("vfs_test")
    path = os.path.join(os.getcwd(), "vfs_test")

    return_code = True
    for file_sys in filesystems:
        logger.info("Formatting %s to %s ..." %
                         (device, file_sys), terminal_print=False)
        command.run_cmd("umount %s" % device, ignore_errors=True)
        command.run_cmd("mkfs -t %s -F %s" % (file_sys, device))
        command.run_cmd("mount -t %s %s %s" %
                             (file_sys, device, "vfs_test"))
        logger.info("Starting sequential vfs IO test...")
        opts = "-direct=1 -iodepth 4 -rw=rw -rwmixread=50 -name=directoy -runtime=300"
        if not do_fio(logger, command, path, size, opts):
            return_code = False
            break

        logger.info("Starting rand vfs IO test...")
        opts = "-direct=1 -iodepth 4 -rw=randrw -rwmixread=50 -name=directoy -runtime=300"
        if not do_fio(logger, command, path, size, opts):
            return_code = False
            break

    command.run_cmd("umount %s" % device)
    shutil.rmtree("vfs_test")
    return return_code


def do_fio(logger, command, filepath, size, option):
    """
    Fio test
    """
    if os.path.isdir(filepath):
        file_opt = "-directory=%s" % filepath
    else:
        file_opt = "-filename=%s" % filepath
    max_bs = 64
    a_bs = 4
    while a_bs <= max_bs:
        cmd_result = command.run_cmd(
            "fio %s -size=%dK -bs=%dK %s" % (file_opt, size, a_bs, option))
        if cmd_result[2] != 0:
            logger.error("%s fio failed." % filepath)
            return False
        a_bs = a_bs * 2
    logger.info("%s fio succeed." % filepath)
    return True


def valid_disk(logger, disk, disks):
    """
    Is the disk valid
    """
    result = True
    if disk:
        if disk != "all" and disk not in disks:
            logger.error("%s is in use or disk does not exist." % disk)
            result = False
    else:
        logger.error("Failed to get disk information.")
        result = False
    return result
