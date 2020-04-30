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


class CertEnv:
    environmentfile = "/etc/eulercert.json"
    releasefile = "/etc/os-release"
    datadirectory = "/var/eulercert"
    certificationfile = datadirectory + "/certification.json"
    devicefile = datadirectory + "/device.json"
    factoryfile = datadirectory + "/factory.json"
    rebootfile = datadirectory + "/reboot.json"
    testdirectoy = "/usr/share/eulercert/lib/tests"
    logdirectoy = "/usr/share/eulercert/logs"
    resultdirectoy = "/usr/share/eulercert/lib/server/results"
    kernelinfo = "/usr/share/eulercert/kernelrelease.json"


