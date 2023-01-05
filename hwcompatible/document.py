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

import os
import json
import configparser
import copy
from subprocess import getoutput
from .command_ui import CommandUI
from .device import Device
from .sysinfo import SysInfo
from .env import CertEnv
from .constants import FILE_FLAGS, FILE_MODES


class Document():
    """
    Basic document module
    """

    def __init__(self, filename, logger, document=None):
        self.filename = filename
        self.logger = logger
        self.document = document

    def save(self):
        """
        Save file
        """
        with os.fdopen(os.open(self.filename, FILE_FLAGS, FILE_MODES), "w+") as save_f:
            json.dump(self.document, save_f, indent=4)
        return True

    def load(self):
        """
        Load file
        """
        if not os.path.exists(self.filename):
            return False

        try:
            with open(self.filename, "r") as load_f:
                self.document = json.load(load_f)
        except json.decoder.JSONDecodeError as error:
            self.logger.error("The file %s is not json file." % self.filename)
            return False

        return True


class CertDocument(Document):
    """
    Get hardware and release information
    """

    def __init__(self, filename, logger, document=''):
        super().__init__(filename, logger, dict())
        if not document:
            self.load()

    def new(self):
        """
        Create new document object
        """
        try:
            cmd_result = getoutput("/usr/sbin/dmidecode -t 1")
            for line in cmd_result.split("\n"):
                property_right = line.split(":", 1)
                if len(property_right) != 2:
                    continue
                key = property_right[0].strip()
                value = property_right[1].strip()
                if key in ("Manufacturer", "Product Name", "Version"):
                    self.document[key] = value
        except Exception as concrete_error:
            self.logger.error(
                "Get hardware information failed. %s" % concrete_error)

        if not os.path.exists(CertEnv.releasefile):
            self.logger.error("The file %s doesn't exist." %
                              CertEnv.releasefile)
            return False

        sysinfo = SysInfo(CertEnv.releasefile)
        self.document["OS"] = sysinfo.get_product() + " " + sysinfo.get_version()
        self.document["kernel"] = sysinfo.get_kernel()
        self.document["ID"] = CommandUI().prompt(
            "Please provide your Compatibility Test ID:")
        self.document["Product URL"] = CommandUI().prompt(
            "Please provide your Product URL:")
        self.document["server"] = CommandUI().prompt(
            "Please provide the Compatibility Test Server (Hostname or Ipaddr):")

    def get_oech_value(self, prop, value):
        """
        Get oech version or name
        """
        config = configparser.ConfigParser()
        config.read(CertEnv.versionfile)
        if prop == 'VERSION':
            self.document["oech_version"] = config.get(prop, value)
        self.document["oech_name"] = config.get(prop, value)
        return config.get(prop, value)

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
        return self.document["OS"]

    def get_server(self):
        """
        Get server information
        """
        return self.document["server"]

    def get_url(self):
        """
        Get url
        """
        return self.document["Product URL"]

    def get_certify(self):
        """
        Get certify
        """
        return self.document["ID"]

    def get_kernel(self):
        """
        Get kernel information
        """
        return self.document["kernel"]


class DeviceDocument(Document):
    """
    Get device document
    """

    def __init__(self, filename, logger, devices=''):
        super().__init__(filename, logger, list())
        if not devices:
            self.load()
            return
        for device in devices:
            self.document.append(device.properties)
           

class FactoryDocument(Document):
    """
    Get factory from file or factory parameter
    """

    def __init__(self, filename, logger, factory=''):
        super().__init__(filename, logger, list())
        if not factory:
            self.load()
            return
        for member in factory:
            element = copy.copy(member)
            element["device"] = member["device"].properties
            self.document.append(element)

    def get_factory(self):
        """
        Get factory parameter information
        :return:
        """
        factory = list()
        for element in self.document:
            test = element
            device = Device(element["device"], self.logger)
            test["device"] = device
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
        with open(self.filename) as fp_info:
            self.config = fp_info.readlines()
            for line in self.config:
                if line.strip() and line.strip()[0] == "#":
                    continue
                words = line.strip().split(" ")
                if words[0]:
                    self.parameters[words[0]] = " ".join(words[1:])

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

    def add_parameter(self, name, value):
        """
        Add parameter
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
        with os.fdopen(os.open(self.filename, FILE_FLAGS, FILE_MODES), "w") as fp_info:
            for line in self.config:
                fp_info.write(line)