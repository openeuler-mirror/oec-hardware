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


class CertEnv:
    """
    Certification file path
    """

    environmentfile = "/etc/oech.json"
    releasefile = "/etc/os-release"
    datadirectory = "/var/oech"
    certificationfile = os.path.join(datadirectory, "compatibility.json")
    devicefile = os.path.join(datadirectory, "device.json")
    factoryfile = os.path.join(datadirectory, "factory.json")
    virtfactoryfile = os.path.join(datadirectory, "virtfactory.json")
    rebootfile = os.path.join(datadirectory, "reboot.json")
    testdirectoy = "/usr/share/oech/lib/tests"
    logdirectoy = "/usr/share/oech/logs"
    resultdirectoy = "/usr/share/oech/lib/server/results"
    kernelinfo = "/usr/share/oech/kernelrelease.json"
    versionfile = "/usr/share/oech/lib/config/version.config"
    pcifile = "/usr/share/hwdata/pci.ids"
    oechpcifile = "/usr/share/oech/lib/config/pci.ids"
    configfile = "/usr/share/oech/lib/config/test_config.yaml"
