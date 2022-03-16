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

"""Document processing"""

import json
from .commandUI import CommandUI
from .command import Command
from .device import Device
from .sysinfo import SysInfo
from .env import CertEnv
from .constants import *


class Document():
    """
    Read and write documents
    """

    def __init__(self, filename, document=''):
        self.document = document
        self.filename = filename

    def new(self):
        print("doc new")

    def save(self):
        """save file"""
        try:
            with open(self.filename, "w+") as save_f:
                json.dump(self.document, save_f, indent=4)
                save_f.close()
        except Exception as concrete_error:
            print("Error: doc save fail.\n", concrete_error)
            return False
        return True

    def load(self):
        """load file"""
        try:
            with open(self.filename, "r") as load_f:
                self.document = json.load(load_f)
                load_f.close()
        except Exception:
            return False
        return True


class CertDocument(Document):
    """
    get hardware and release information
    """

    def __init__(self, filename, document=''):
        self.document = dict()
        self.filename = filename
        if not document:
            self.load()
        else:
            self.documemt = document

    def new(self):
        """
        new document object
        """
        try:
            pipe = Command("/usr/sbin/dmidecode -t 1")
            pipe.start()
            self.document = dict()
            while True:
                line = pipe.readline()
                if not line:
                    break
                property_right = line.split(":", 1)
                if len(property_right) != 2:
                    continue
                key = property_right[0].strip()
                value = property_right[1].strip()
                if key in ["Manufacturer", "Product Name", "Version"]:
                    self.document[key] = value
        except Exception as concrete_error:
            print("Error: get hardware info fail.\n", concrete_error)

        sysinfo = SysInfo(CertEnv.releasefile)
        self.document[OS] = sysinfo.product + " " + sysinfo.get_version()
        self.document[KERNEL] = sysinfo.kernel
        self.document[ID] = CommandUI().prompt(
            "Please provide your Compatibility Test ID:")
        self.document[PRODUCTURL] = CommandUI().prompt(
            "Please provide your Product URL:")
        self.document[SERVER] = CommandUI().prompt("Please provide the Compatibility Test "
                                                   "Server (Hostname or Ipaddr):")

    def get_hardware(self):
        """
        Get hardware information
        """
        return self.document["Manufacturer"] + " " + self.document["Product Name"] + " " \
            + self.document["Version"]

    def get_os(self):
        """
        Get os information
        """
        return self.document[OS]

    def get_server(self):
        """
        Get server information
        """
        return self.document[SERVER]

    def get_url(self):
        """
        Get url
        """
        return self.document[PRODUCTURL]

    def get_certify(self):
        """
        Get certify
        """
        return self.document[ID]

    def get_kernel(self):
        """
        Get kernel information
        """
        return self.document[KERNEL]


class DeviceDocument(Document):
    """
    get device document
    """

    def __init__(self, filename, devices=''):
        self.filename = filename
        self.document = list()
        if not devices:
            self.load()
        else:
            for device in devices:
                self.document.append(device.properties)


class FactoryDocument(Document):
    """
    get factory from file or factory parameter
    """

    def __init__(self, filename, factory=''):
        self.document = list()
        self.filename = filename
        if not factory:
            self.load()
            return
        for member in factory:
            element = dict()
            element[NAME] = member[NAME]
            element[DEVICE] = member[DEVICE].properties
            element[RUN] = member[RUN]
            element[STATUS] = member[STATUS]
            self.document.append(element)

    def get_factory(self):
        """
        Get factory parameter information
        :return:
        """
        factory = list()
        for element in self.document:
            test = dict()
            device = Device(element[DEVICE])
            test[DEVICE] = device
            test[NAME] = element[NAME]
            test[RUN] = element[RUN]
            test[STATUS] = element[STATUS]
            factory.append(test)
        return factory


class ConfigFile:
    """
    Get parameters from configuration file
    """

    def __init__(self, filename):
        self.filename = filename
        self.parameters = dict()
        self.config = list()
        self.load()

    def load(self):
        """
        Load config file
        """
        fp_info = open(self.filename)
        self.config = fp_info.readlines()
        for line in self.config:
            if line.strip() and line.strip()[0] == "#":
                continue
            words = line.strip().split(" ")
            if words[0]:
                self.parameters[words[0]] = " ".join(words[1:])
        fp_info.close()

    def get_parameter(self, name):
        """
        Get parameter
        """
        return self.parameters.get(name, None)

    def dump(self):
        """
        Dump
        """
        for line in self.config:
            string = line.strip()
            if not string or string[0] == "#":
                continue
            print(string)

    def add_parameter(self, name, value):
        """
        add parameter
        """
        if self.get_parameter(name):
            return False
        self.parameters[name] = value
        self.config.append("%s %s\n" % (name, value))
        self.save()
        return True

    def remove_parameter(self, name):
        """
        Update configuration information
        :param name:
        :return:
        """
        if not self.get_parameter(name):
            return
        del self.parameters[name]
        newconfig = list()
        for line in self.config:
            if line.strip() and line.strip()[0] == "#":
                newconfig.append(line)
                continue
            words = line.strip().split(" ")
            if words and words[0] == name:
                continue
            else:
                newconfig.append(line)
        self.config = newconfig
        self.save()

    def save(self):
        """
        Save the config property value to a file
        :return:
        """
        fp_info = open(self.filename, "w")
        for line in self.config:
            fp_info.write(line)
        fp_info.close()
