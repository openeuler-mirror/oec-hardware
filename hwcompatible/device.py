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

import re
from .command import Command
from .constants import FC, GPU, VGPU, RAID, NVME


def filter_char(string):
    """
    Fileter character
    :param string:update_factory
    :return:
    """
    ascii_blacklist = map(chr, range(9) + range(11, 13) + range(14, 32))
    filtered = u''
    start = 0
    for i in range(len(string)):
        char_filter = string[i]
        if char_filter in ascii_blacklist or (type(string) != unicode and ord(char_filter) >= 128):
            if start < i:
                filtered += string[start:i]
            start = i + 1
    filtered += string[start:]
    return filtered


class CertDevice:
    """
    Certified device
    """

    def __init__(self, logger):
        self.logger = logger
        self.devices = None

    def get_devices(self):
        """
        Get devices information
        :return:
        """
        self.devices = list()
        try:
            pipe = Command("udevadm info --export-db")
            pipe.start()
            properties = dict()
            while True:
                line = pipe.readline()
                if not line:
                    break
                if line == "\n" and len(properties) > 0:
                    device = Device(properties)
                    if device.path != "":
                        self.devices.append(device)
                    properties = dict()
                else:
                    prop = line.split(":", 1)
                    if len(prop) == 2:
                        tp = prop[0].strip('\ \'\n')
                        attribute = prop[1].strip('\ \'\n')
                        if tp == "E":
                            keyvalue = attribute.split("=", 1)
                            if len(keyvalue) == 2:
                                properties[keyvalue[0]] = keyvalue[1]
                        elif tp == "P":
                            properties["INFO"] = attribute
        except Exception as e:
            self.logger.warning("Get devices failed.\n")
        self.devices.sort(key=lambda k: k.path)
        return self.devices


class Device:
    """
    Device properties
    """

    def __init__(self, properties=None):
        self.path = ""
        self.pci = ""
        self.quad = list()
        self.driver = ""
        self.driver_version = ""
        self.chip = ""
        self.board = ""
        self.file = ""
        if properties:
            self.properties = properties
            self.path = properties["DEVPATH"]
        else:
            self.properties = dict()

    def get_property(self, prop):
        """
        get properties
        :param prop:
        :return:
        """
        return self.properties.get(prop, "")

    def get_name(self):
        """
        get property value
        :return:
        """
        if "INTERFACE" in self.properties.keys():
            return self.properties.get("INTERFACE")
        if "DEVNAME" in self.properties.keys():
            return self.properties.get("DEVNAME").split("/")[-1]
        if self.path:
            return self.path.split("/")[-1]
        return ""

    def get_model(self, name, file):
        """
        get board model name
        :return:
        """
        self.file = file
        self.file.seek(0)
        # get PCI number
        if not self.get_pci():
            return self.board, self.chip
        # get quadruple
        self.get_quadruple()
        if name == FC:
            self.get_fc_card()
        elif name == GPU or name == VGPU:
            self.get_gpu_card()
        elif name == RAID:
            self.get_raid_card()
        elif name == NVME:
            self.get_nvme_card()
        else:
            # 8080 indicate intel
            if self.quad[0] == "8086":
                self.get_nic_intel()
            # 15b3 indicate mellanox
            if self.quad[0] == "15b3":
                self.get_nic_mellanox()
            # 14e4 indicate Broadcom
            if self.quad[0] == "14e4":
                self.get_nic_broadcom()
            # 19e5 indicate huawei
            if self.quad[0] == "19e5":
                self.get_nic_huawei()
            # 8088 indicate Netswift
            if self.quad[0] == "8088":
                self.get_nic_netswift()
        self._is_null()
        return self.board, self.chip

    def get_raid_card(self):
        """
        get the board model and chip model of raid card
        """
        flag = 0
        for ln in self.file.readlines():
            if flag == 0:
                if re.match(self.quad[0], ln):
                    flag += 1
            elif flag == 1:
                if re.match("\t" + self.quad[1], ln):
                    flag += 1
                    result = re.search(r"\b(SAS\S*)\s*", ln)
                    if result:
                        self.chip = result.group(1)
                    if len(self.chip) < 7:
                        result = re.search(r"(\bSAS\S* \S*)\s*", ln)
                        if result:
                            self.chip = result.group(1)
                    if not self.chip:
                        self.chip = ln.replace(ln[0:7], "").strip()
            elif flag == 2:
                if re.match("\t\t" + self.quad[2] + " " + self.quad[3], ln):
                    self.board = ln.split(" ")[-1].strip()
                    break

    def get_fc_card(self):
        """
        get the board model and chip model of FC card
        """
        flag = 0
        for ln in self.file.readlines():
            if flag == 0:
                if re.match(self.quad[0], ln):
                    flag += 1
            elif flag == 1:
                if re.match("\t" + self.quad[1], ln):
                    flag += 1
                    self.chip = ln.strip().split(" ")[2]
            elif flag == 2:
                if re.match("\t\t" + self.quad[2] + " " + self.quad[3], ln):
                    flag += 1
                    if self.quad[0] == "19e5":
                        self.board = ln.strip().split(" ")[4].strip()
                    else:
                        self.board = ln.strip().split(" ")[3].strip()
                    break

    def get_nvme_card(self):
        """
        get the board model and chip model of nvme card
        """
        flag = 0
        for ln in self.file.readlines():
            if flag == 0:
                if re.match(self.quad[0], ln):
                    flag += 1
            elif flag == 1:
                if re.match("\t" + self.quad[1], ln):
                    flag += 1
                    if self.quad[0] == "8086":
                        self.chip = re.search(r'\[(.*)\]', ln).group(1)
                    elif self.quad[0] == "19e5":
                        self.chip = re.sub(ln[0:7], "", ln).split(" ")[0]
                    else:
                        self.chip = ln.split(" ")[-1]
            elif flag == 2:
                if re.match("\t\t" + self.quad[2] + " " + self.quad[3], ln):
                    flag += 1
                    if self.quad[0] == "8086":
                        self.board = re.search(r'\((.*)\)', ln).group(1)
                    else:
                        self.board = re.search(
                            r'(\b(?:SP|ES|PM|SM)\S*)', ln).group(1)
                    break

    def get_nic_intel(self):
        """
        get the board model and chip model of intel card
        """
        flag = 0
        for ln in self.file.readlines():
            if flag == 0:
                if re.match(self.quad[0], ln):
                    flag += 1
            elif flag == 1:
                if re.match("\t" + self.quad[1], ln):
                    flag += 1
                    info = ln.replace(self.quad[1], "").strip()
                    self.chip = re.search(r'(\S+[0-9]{3,6}\S*)', info).group(1)
            else:
                if re.match("\t\t" + self.quad[2] + " " + self.quad[3], ln):
                    info = ln.replace(
                        self.quad[2] + " " + self.quad[3], "").strip()
                    tmp = re.search(r'(\S*[0-9]{3,6}\S*)', info)
                    if tmp:
                        self.board = tmp.group(1)
                    if not self.board:
                        self.board = info.strip()
                    break

    def get_nic_broadcom(self):
        """
        get the board model and chip model of broadcom nic card
        """
        flag = 0
        for ln in self.file.readlines():
            if flag == 0:
                if re.match(self.quad[0], ln):
                    flag += 1
            elif flag == 1:
                if re.match("\t" + self.quad[1], ln):
                    flag += 1
                    self.chip = re.search(r'(\bBCM\S*)', ln).group(1)
            else:
                if re.match("\t\t" + self.quad[2] + " " + self.quad[3], ln):
                    self.board = re.search(r'(\b(?:BCM|QLE)\S*)', ln).group(1)
                    break

    def get_nic_huawei(self):
        """
        get the board model and chip model of intel card
        """
        flag = 0
        for ln in self.file.readlines():
            if flag == 0:
                if re.match(self.quad[0], ln):
                    flag += 1
            elif flag == 1:
                if re.match("\t" + self.quad[1], ln):
                    flag += 1
                    hns = re.search(r'(HNS\s*\S*)\s*', ln)
                    if hns:
                        self.chip = hns.group(1)
                    if not self.chip:
                        self.chip = ln.strip().split(" ")[2]
            else:
                if re.match("\t\t" + self.quad[2] + " " + self.quad[3], ln):
                    self.board = re.search(r'(\b(?:SP|TM)\S*)', ln).group(1)
                    break

    def get_nic_netswift(self):
        """
        get the board model and chip model of netswift card
        """
        flag = 0
        for ln in self.file.readlines():
            if flag == 0:
                if re.match(self.quad[0], ln):
                    flag += 1
            elif flag == 1:
                if re.match("\t" + self.quad[1], ln):
                    flag += 1
                    self.chip = re.search(r'(RP\S*)', ln).group(1)
            else:
                if re.match("\t\t" + self.quad[2] + " " + self.quad[3], ln):
                    self.board = re.search(r'(RP\S*)', ln).group(1)
                    break

    def get_broadcom_card(self):
        """
        get the board model and chip model of broadcom card
        """
        flag = 0
        for ln in self.file.readlines():
            if flag == 0:
                if re.match(self.quad[1], ln):
                    flag += 1
            elif flag == 1:
                if re.match(self.quad[0], ln):
                    flag += 1
                    chip_info = ln.replace("{0} {1}  ".format(
                        self.quad[0], self.quad[1]), "")
                    self.chip = re.match(
                        r'\s*(\w*\d{4}\w*)\s*', chip_info).group(1)
            else:
                if re.match("\t\t" + self.quad[3] + " " + self.quad[2], ln) and ";" in ln:
                    model = ln.split(" ")[2].strip().split(";").strip()
                    self.chip = model[0]
                    self.board = model[1]
                    break
                else:
                    self.board = ln.split(" ")[-1].strip()
                    break

    def get_nic_mellanox(self):
        """
        get the board model and chip model of mellanox card
        """
        flag = 0
        for ln in self.file.readlines():
            if flag == 0:
                if re.match(self.quad[0], ln):
                    flag += 1
            elif flag == 1:
                if re.match("\t" + self.quad[1], ln):
                    flag += 1
                    self.chip = re.search("\[(.*)\]", ln).group(1)
            else:
                if re.match("\t\t" + self.quad[2] + " " + self.quad[3], ln):
                    self.board = re.search(
                        r'(\b(?:SP|SM|MCX)\S*)', ln).group(1)
                    break

    def get_gpu_card(self):
        """
        get the board model and chip model of gpu card
        """
        flag = 0
        for ln in self.file.readlines():
            if flag == 0:
                if re.match(self.quad[0], ln):
                    flag += 1
            elif flag == 1:
                if re.match("\t" + self.quad[1], ln):
                    flag += 1
                    self.chip = ln.strip().split(" ")[2]
            else:
                if re.match("\t\t" + self.quad[2] + " " + self.quad[3], ln):
                    self.board = re.sub(ln[0:11], "", ln).strip()
                    break

    def get_driver(self):
        """
        get the driver name of the board
        :return:
        """
        self.get_pci()
        com = Command("lspci -xs %s -v" % self.pci)
        output = com.read()
        for info in output.split('\n'):
            if re.search("Kernel driver in use|Kernel modules", info):
                self.driver = info.split(":")[1].strip()
                return self.driver
        return ""

    def get_driver_version(self):
        """
        Get the driver version of the board
        :return:
        """
        com = Command("modinfo %s" % self.driver)
        output = com.read()
        for info in output.split('\n'):
            if re.search(r"\bversion:", info):
                self.driver_version = info.split(":", 1)[1].strip()
                return self.driver_version
        return ""

    def set_driver(self, driver):
        self.driver = driver

    def get_pci(self):
        """
        get the pci of card
        :return:
        """
        self.pci = self.properties.get("PCI_SLOT_NAME", "")
        if not self.pci:
            self.pci = self.properties.get("ID_PATH", "")
            if self.pci:
                self.pci = self.pci.split("-")[1]
        return self.pci

    def get_quadruple(self):
        """
        get quadruple by pci number
        :return:
        """
        com = Command("lspci -xs %s" % self.pci)
        output = com.read()
        self.quad = []
        for ln in output.split('\n'):
            if re.match("00: ", ln):
                tmp = ln.split(" ")[1:5]
                self.quad.extend([tmp[1] + tmp[0], tmp[3] + tmp[2]])
            if re.match("20: ", ln):
                tmp = ln.split(" ")[-4:]
                self.quad.extend([tmp[-3] + tmp[-4], tmp[-1] + tmp[-2]])

    def _is_null(self):
        """
        Judge whether the board model and chip signal are empty
        """
        if not self.chip:
            self.chip = "N/A"
        if not self.board:
            self.board = "N/A"
