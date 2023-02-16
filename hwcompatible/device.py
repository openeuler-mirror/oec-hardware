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
from .env import CertEnv


class CertDevice:
    """
    Certified device
    """

    def __init__(self, logger):
        self.logger = logger
        self.devices = None
        self.command = Command(self.logger)

    def get_devices(self):
        """
        Get devices information
        :return:
        """
        self.devices = list()
        cmd_result = self.command.run_cmd(
            "udevadm info --export-db", log_print=False)
        properties = dict()
        try:
            all_lines = cmd_result[0].split("\n")
            for line in all_lines:
                if "P: /" in line and len(properties) > 0:
                    device = Device(properties, self.logger)
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
            self.logger.error("Get devices failed.")

        self.devices.sort(key=lambda k: k.path)
        return self.devices


class Device:
    """
    Device properties
    """

    def __init__(self, properties=None, logger=None):
        self.logger = logger
        self.command = Command(self.logger)
        self.name = ""
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
        self.name = name
        self.file = file
        self.file.seek(0)
        # get PCI number
        if not self.get_pci():
            return self.board, self.chip

        try:
            # get quadruple
            self.get_quadruple()
            if name == "fc":
                self.get_fc_card()
            elif name == "gpu" or name == "vgpu":
                self.get_gpu_card()
            elif name == "raid":
                self.get_raid_card()
            elif name == "nvme" or name == "spdk":
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
        except Exception:
            self.logger.error(
                "Get board information failed, please check %s!" % CertEnv.pcifile, terminal_print=False)

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
                    self.chip = self._search_info(r"\b(SAS\S*)\s*", ln)
                    if len(self.chip) < 7:
                        self.chip = self._search_info(r"(\bSAS\S* \S*)\s*", ln)
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
                        self.chip = self._search_info(r'\[(.*)\]', ln)
                    elif self.quad[0] == "19e5":
                        self.chip = re.sub(ln[0:7], "", ln).split(" ")[0]
                    else:
                        self.chip = ln.split(" ")[-1]
            elif flag == 2:
                if re.match("\t\t" + self.quad[2] + " " + self.quad[3], ln):
                    flag += 1
                    if self.quad[0] == "8086":
                        self.board = self._search_info(r'\((.*)\)', ln)
                    else:
                        self.board = self._search_info(
                            r'(\b(?:SP|ES|PM|SM)\S*)', ln)
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
                    self.chip = self._search_info(r'(\S+[0-9]{3,6}\S*)', info)
            else:
                if re.match("\t\t" + self.quad[2] + " " + self.quad[3], ln):
                    info = ln.replace(
                        self.quad[2] + " " + self.quad[3], "").strip()
                    self.board = self._search_info(r'(\S*[0-9]{3,6}\S*)', info)
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
                    self.chip = self._search_info(r'(\bBCM\S*)', ln)
            else:
                if re.match("\t\t" + self.quad[2] + " " + self.quad[3], ln):
                    self.board = self._search_info(r'(\b(?:BCM|QLE)\S*)', ln)
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
                    self.chip = self._search_info(r'(HNS\s*\S*)\s*', ln)
                    if not self.chip:
                        self.chip = ln.strip().split(" ")[2]
            else:
                if re.match("\t\t" + self.quad[2] + " " + self.quad[3], ln):
                    self.board = self._search_info(r'(\b(?:SP|TM)\S*)', ln)
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
                    self.chip = self._search_info(r'(RP\S*)', ln)
            else:
                if re.match("\t\t" + self.quad[2] + " " + self.quad[3], ln):
                    self.board = self._search_info(r'(RP\S*)', ln)
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
                    val = re.match(r'\s*(\w*\d{4}\w*)\s*', chip_info)
                    self.chip = ""
                    if val:
                        self.chip = val.group(1)
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
                    self.chip = self._search_info("\[(.*)\]", ln)
            else:
                if re.match("\t\t" + self.quad[2] + " " + self.quad[3], ln):
                    self.board = self._search_info(r'(\b(?:SP|SM|MCX)\S*)', ln)
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
        if not self.pci:
            return ""
        cmd_result = self.command.run_cmd(
            "lspci -xs %s -v" % self.pci, log_print=False)
        for info in cmd_result[0].split('\n'):
            if re.search("Kernel driver in use|Kernel modules", info):
                self.driver = info.split(":")[1].strip()
                return self.driver
        return ""

    def get_driver_version(self):
        """
        Get the driver version of the board
        :return:
        """
        if not self.driver:
            return ""
        cmd_result = self.command.run_cmd(
            "modinfo %s" % self.driver, log_print=False)
        for info in cmd_result[0].split('\n'):
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
        cmd_result = self.command.run_cmd(
            "lspci -xs %s" % self.pci, log_print=False)
        self.quad = []
        for ln in cmd_result[0].split('\n'):
            if re.match("00: ", ln):
                tmp = ln.split(" ")[1:5]
                self.quad.extend([tmp[1] + tmp[0], tmp[3] + tmp[2]])
            if re.match("20: ", ln):
                tmp = ln.split(" ")[-4:]
                self.quad.extend([tmp[-3] + tmp[-4], tmp[-1] + tmp[-2]])
        return self.quad

    def _is_null(self):
        """
        Judge whether the board model and chip signal are empty
        """
        if not self.chip:
            self.chip = "N/A"
        if not self.board:
            self.board = "N/A"

    @staticmethod
    def _search_info(restr, line):
        value = re.search(restr, line)
        if value:
            return value.group(1)
        return ""
