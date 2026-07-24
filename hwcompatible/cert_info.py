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
import shlex
from datetime import date
from .env import CertEnv
from .constants import FILE_FLAGS, FILE_MODES

PASSTHROUGH_DRIVERS = {
    "igb-uio",
    "pci-stub",
    "uio-pci-generic",
    "vfio-pci",
}


class CertInfo:
    def __init__(self, logger, command):
        self.cert_devices = []
        self.cert_quads = []
        self.infos = ["vendorID", "deviceID", "svID", "ssID", "architecture", "os", "driverName", "version",
                      "type", "date", "sha256", "driverSize", "chipVendor", "boardModel", "chipModel", "item",
                      "downloadLink"]
        self.logger = logger
        self.command = command

    @staticmethod
    def _normalize_driver_name(driver):
        return driver.strip().replace("_", "-")

    def _get_driver_candidates(self, device):
        """Return driver modules in the order they should be inspected."""
        driver = getattr(device, "driver", "").strip()
        modules = getattr(device, "kernel_modules", [])
        modules = [module.strip() for module in modules if module.strip()]

        if self._normalize_driver_name(driver) in PASSTHROUGH_DRIVERS:
            candidates = modules + [driver]
        else:
            candidates = [driver] + modules

        result = []
        seen = set()
        for candidate in candidates:
            normalized = self._normalize_driver_name(candidate)
            if not candidate or normalized in seen:
                continue
            seen.add(normalized)
            result.append(candidate)
        return result

    def _get_driver_file(self, device_name, device):
        """Return the selected driver module and its file path."""
        candidates = self._get_driver_candidates(device)
        current_driver = getattr(device, "driver", "").strip()
        current_is_passthrough = (
            self._normalize_driver_name(current_driver) in PASSTHROUGH_DRIVERS)
        builtin_driver = ""

        self.logger.info(
            "Start to collect driver file information for %s, candidates: %s."
            % (device_name, ", ".join(candidates)))
        for driver in candidates:
            filename = self.command.run_cmd(
                "modinfo -F filename %s" % shlex.quote(driver),
                log_print=False, timeout=30)
            if filename[2] != 0 or not filename[0].strip():
                continue

            driver_file = filename[0].strip()
            if driver_file == "(builtin)":
                if driver == current_driver and not current_is_passthrough:
                    return driver, ""
                if not builtin_driver:
                    builtin_driver = driver
                continue
            return driver, driver_file

        if builtin_driver:
            return builtin_driver, ""
        return current_driver, ""

    def _get_driver_version(self, selected_driver, device):
        """Get the version belonging to the selected driver module."""
        if not selected_driver:
            return ""
        if selected_driver == getattr(device, "driver", ""):
            return getattr(device, "driver_version", "")

        version = self.command.run_cmd(
            "modinfo -F version %s" % shlex.quote(selected_driver),
            log_print=False, timeout=30)
        if version[2] == 0:
            return version[0].strip()
        return ""

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
        chip_vendor = self.command.run_cmd(
            "grep '^%s' %s | cut -d ' ' -f 3" % (device.quad[0], CertEnv.pcifile), log_print=False)
        oec_json["chipVendor"] = chip_vendor[0].strip("\n")
        oec_json["boardModel"] = device.board
        oec_json["chipModel"] = device.chip
        oec_json["type"] = device_name.upper()
        if oec_json["type"] == "ETHERNET":
            oec_json["type"] = "NIC"
        arch = self.command.run_cmd("uname -m", log_print=False)
        oec_json["architecture"] = arch[0].strip("\n")
        os_cmd = self.command.run_cmd(
            "grep openeulerversion /etc/openEuler-latest | cut -d '=' -f 2", log_print=False)
        os_version = os_cmd[0].strip("\n").replace('-', ' ')
        oec_json["os"] = os_version
        curday = date.today().strftime("%Y-%m-%d")
        oec_json["date"] = curday
        selected_driver, driver_file = self._get_driver_file(device_name, device)
        oec_json["driverName"] = selected_driver
        oec_json["version"] = self._get_driver_version(selected_driver, device)
        if not driver_file:
            self.logger.warning(
                "Failed to get driver filename for %s, driver: %s. "
                "Please fill sha256, driverSize and downloadLink manually."
                % (device_name, selected_driver))
        else:
            self.logger.info(
                "Driver file for %s, driver: %s is %s. "
                "Start to calculate sha256."
                % (device_name, selected_driver, driver_file))
            shanum = self.command.run_cmd(
                "sha256sum %s" % shlex.quote(driver_file),
                log_print=False, timeout=120)
            if shanum[2] == 0 and shanum[0].strip():
                oec_json["sha256"] = shanum[0].split()[0]
                self.logger.info("Calculate driver sha256 for %s succeed." % device_name)
            else:
                self.logger.warning(
                    "Calculate driver sha256 for %s failed. Please fill it manually."
                    % device_name)

            self.logger.info("Start to get driver size for %s." % device_name)
            driver_size = self.command.run_cmd(
                "ls -lh %s" % shlex.quote(driver_file),
                log_print=False, timeout=30)
            size_info = driver_size[0].split()
            if driver_size[2] == 0 and len(size_info) >= 5:
                oec_json["driverSize"] = size_info[4]
                self.logger.info("Get driver size for %s succeed." % device_name)
            else:
                self.logger.warning(
                    "Get driver size for %s failed. Please fill it manually."
                    % device_name)
        oec_json["item"] = ""
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
