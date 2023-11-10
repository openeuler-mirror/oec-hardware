#!/usr/bin/env python3
# coding: utf-8
# oec-hardware is licensed under the Mulan PSL v2.gica's
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Author: @meitingli
# Create: 2022-08-24
# Desc: Generate compatibility json file

import os
import json
from datetime import date
from .env import CertEnv
from .constants import FILE_FLAGS, FILE_MODES


class CertInfo:
    def __init__(self, logger, command):
        self.cert_devices = []
        self.cert_quads = []
        self.infos = ["vendorID", "deviceID", "svID", "ssID", "architecture", "os", "driverName", "version",
                      "type", "date", "sha256", "driverSize", "chipVendor", "boardModel", "chipModel", "downloadLink"]
        self.logger = logger
        self.command = command

    def create_json(self, device_name, device):
        """
        Create hardware information json
        Args:
            device_name: device name
            device: hardware device
        Returns: True/False
        """
        if not device or not device.quad:
            self.logger.warning(
                "The %s doesn't have quadruple information, couldn't get hardware." % device_name)
            return False

        if device.quad in self.cert_quads:
            return True

        oec_json = {}
        for info in self.infos:
            oec_json[info] = ""

        self.logger.info(
            "Please input sha256, driverSize, downloadLink for %s manually "
            "if you use outbox driver." % device_name)

        oec_json["vendorID"] = device.quad[0]
        oec_json["deviceID"] = device.quad[1]
        oec_json["svID"] = device.quad[2]
        oec_json["ssID"] = device.quad[3]
        oec_json["driverName"] = device.driver
        oec_json["version"] = device.driver_version
        chip_vendor = self.command.run_cmd(
            "grep '^%s' %s | cut -d ' ' -f 3" % (device.quad[0], CertEnv.pcifile), log_print=False)
        oec_json["chipVendor"] = chip_vendor[0].strip("\n")
        oec_json["boardModel"] = device.board
        oec_json["chipModel"] = device.chip
        oec_json["type"] = device_name.upper()
        arch = self.command.run_cmd("uname -m", log_print=False)
        oec_json["architecture"] = arch[0].strip("\n")
        os_cmd = self.command.run_cmd(
            "grep openeulerversion /etc/openEuler-latest | cut -d '=' -f 2", log_print=False)
        os_version = os_cmd[0].strip("\n").replace('-', ' ')
        oec_json["os"] = os_version
        curday = date.today().strftime("%Y.%m.%d")
        oec_json["date"] = curday
        filename = self.command.run_cmd(
            "modinfo %s | grep filename | awk '{print $2}'" % device.driver, log_print=False)
        shanum = self.command.run_cmd(
            "sha256sum %s | awk '{print $1}'" % filename[0].strip("\n"), log_print=False)
        oec_json["sha256"] = shanum[0].strip("\n")
        driver_size = self.command.run_cmd(
            "ls -lh %s | awk '{print $5}'" % filename[0].strip("\n"), log_print=False)
        oec_json["driverSize"] = driver_size[0].strip("\n")
        oec_json["downloadLink"] = "inbox"

        self.cert_quads.append(device.quad)
        self.cert_devices.append(oec_json)
        return True

    def export_cert_info(self):
        """
        Export device cert informations to json file
        """
        if not self.cert_devices:
            self.logger.info("There is no cert device need to export.")
            return

        name = "hw_compatibility.json"
        file = os.path.join(self.logger.logdir, name)
        with os.fdopen(os.open(file, FILE_FLAGS, FILE_MODES), "w", encoding='utf-8') as fd_cert:
            fd_cert.write(json.dumps(self.cert_devices, indent=4))

        self.logger.info("The cert device json file is created succeed.")
