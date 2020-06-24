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

import json

from .commandUI import CommandUI
from .command import Command, CertCommandError
from .device import Device
from .sysinfo import SysInfo
from .env import CertEnv


class Document:
    def __init__(self, filename, document=''):
        self.document = document
        self.filename = filename

    def new(self):
        print("doc new")

    def save(self):
        try:
            with open(self.filename, "w+") as save_f:
                json.dump(self.document, save_f, indent=4)
                save_f.close()
        except (IOError, ValueError) as e:
            print("Error: doc save fail.")
            print(e)
            return False
        return True

    def load(self):
        try:
            with open(self.filename, "r") as load_f:
                self.document = json.load(load_f)
                load_f.close()
                return True
        except (IOError, json.decoder.JSONDecodeError):
            return False


class CertDocument(Document):
    def __init__(self, filename, document=''):
        super(CertDocument, self).__init__(filename, document)
        self.document = dict()
        self.filename = filename
        if not document:
            self.load()
        else:
            self.documemt = document

    def new(self):
        try:
            pipe = Command("/usr/sbin/dmidecode -t 1")
            pipe.start()
            self.document = dict()
            while True:
                line = pipe.readline()
                if line:
                    property_right = line.split(":", 1)
                    if len(property_right) == 2:
                        key = property_right[0].strip()
                        value = property_right[1].strip()
                        if key in ["Manufacturer", "Product Name", "Version"]:
                            self.document[key] = value
                else:
                    break
        except OSError as e:
            print("Error: get hardware info fail.")
            print(e)

        sysinfo = SysInfo(CertEnv.releasefile)
        self.document["OS"] = sysinfo.product + " " + sysinfo.get_version()
        self.document["kernel"] = sysinfo.kernel
        self.document["ID"] = CommandUI().prompt("Please provide your Compatibility Test ID:")
        self.document["Product URL"] = CommandUI().prompt("Please provide your Product URL:")
        self.document["server"] = CommandUI().prompt("Please provide the Compatibility Test Server (Hostname or Ipaddr):")

    def get_hardware(self):
        return self.document["Manufacturer"] + " " + self.document["Product Name"] + " " + self.document["Version"]

    def get_os(self):
        return self.document["OS"]

    def get_server(self):
        return self.document["server"]

    def get_url(self):
        return self.document["Product URL"]

    def get_certify(self):
        return self.document["ID"]

    def get_kernel(self):
        return self.document["kernel"]


class DeviceDocument(Document):
    def __init__(self, filename, devices=''):
        super(DeviceDocument, self).__init__(filename, devices)
        self.filename = filename
        self.document = list()
        if not devices:
            self.load()
        else:
            for device in devices:
                self.document.append(device.properties)


class FactoryDocument(Document):
    def __init__(self, filename, factory=''):
        super(FactoryDocument, self).__init__(filename, factory)
        self.document = list()
        self.filename = filename
        if not factory:
            self.load()
        else:
            for member in factory:
                element = dict()
                element["name"] = member["name"]
                element["device"] = member["device"].properties
                element["run"] = member["run"]
                element["status"] = member["status"]
                self.document.append(element)

    def get_factory(self):
        factory = list()
        for element in self.document:
            test = dict()
            device = Device(element["device"])
            test["device"] = device
            test["name"] = element["name"]
            test["run"] = element["run"]
            test["status"] = element["status"]
            factory.append(test)
        return factory


class ConfigFile:
    def __init__(self, filename):
        super(ConfigFile, self).__init__(filename)
        self.filename = filename
        self.parameters = dict()
        self.config = list()
        self.load()

    def load(self):
        fp = open(self.filename)
        self.config = fp.readlines()
        for line in self.config:
            if line.strip() and line.strip()[0] == "#":
                continue
            words = line.strip().split(" ")
            if words[0]:
                self.parameters[words[0]] = " ".join(words[1:])
        fp.close()

    def get_parameter(self, name):
        if self.parameters:
            try:
                return self.parameters[name]
            except KeyError:
                pass
        return None

    def dump(self):
        for line in self.config:
            string = line.strip()
            if not string or string[0] == "#":
                continue
            print(string)

    def add_parameter(self, name, value):
        if not self.getParameter(name):
            self.parameters[name] = value
            self.config.append("%s %s\n" % (name, value))
            self.save()
            return True
        return False

    def remove_parameter(self, name):
        if self.getParameter(name):
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
        fp = open(self.filename, "w")
        for line in self.config:
            fp.write(line)
        fp.close()
