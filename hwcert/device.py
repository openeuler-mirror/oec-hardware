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

from .command import Command, CertCommandError


def filter_char(str):
    ascii_blacklist = map(chr, range(9) + range(11,13) + range(14,32))
    filtered = u''
    start = 0
    for i in range(len(str)):
        c = str[i]
        if c in ascii_blacklist or (type(str) != unicode and ord(c) >= 128):
            if start < i:
                filtered += str[start:i]
            start = i+1
    filtered += str[start:]
    return filtered

class CertDevice:
    def __init__(self):
        self.devices = None

    def get_devices(self):
        self.devices = list()
        try:
            pipe = Command("udevadm info --export-db")
            pipe.start()
            properties = dict()
            while True:
                line = pipe.readline()
                if line:
                    if line == "\n":
                        if len(properties) > 0:
                            device = Device(properties)
                            if device.path != "":
                                self.devices.append(device)
                            properties = dict()
                    else:
                        property = line.split(":", 1)
                        if len(property) == 2:
                            type = property[0].strip('\ \'\n')
                            attribute = property[1].strip('\ \'\n')
                            if type == "E":
                                keyvalue = attribute.split("=", 1)
                                if len(keyvalue) == 2:
                                    properties[keyvalue[0]]= keyvalue[1]
                            elif type == "P":
                                properties["INFO"] = attribute
                else:
                    break
        except Exception as e:
            print("Warning: get devices fail")
            print(e)
        self.devices.sort(key=lambda k: k.path)
        return self.devices

class Device:
    def __init__(self, properties=None):
        self.path = ""
        if properties:
            self.properties = properties
            self.path = properties["DEVPATH"]
        else:
            self.properties = dict()

    def get_property(self, property):
        try:
            return self.properties[property]
        except KeyError:
            return ""

    def get_name(self):
        if "INTERFACE" in self.properties.keys():
            return self.properties["INTERFACE"]
        elif "DEVNAME" in self.properties.keys():
            return self.properties["DEVNAME"].split("/")[-1]
        elif self.path:
            return self.path.split("/")[-1]
        else:
            return ""

