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
import time
import argparse
import shutil
import datetime
import re
from collections import namedtuple

from .document import CertDocument, DeviceDocument, FactoryDocument
from .env import CertEnv
from .device import CertDevice, Device
from .command import Command
from .command_ui import CommandUI
from .job import Job
from .reboot import Reboot
from .client import Client
from .common import create_test_suite, copy_pci, search_factory
from .constants import NODEVICE, GPU_DRIVER, IB, CDTYPES, KEYCARD_VENDORS, \
    BOARD, VERSION, DRIVER, CHIP, DEVICE_INFO


class EulerCertification():
    """
    Main program of oec-hardware
    """

    def __init__(self, logger):
        self.certification = None
        self.test_factory = list()
        self.devices = None
        self.ui = CommandUI()
        self.client = None
        self.dir_name = None
        self.logger = logger
        self.command = Command(logger)

    def run(self):
        """
        Openeuler compatibility verification
        :return:
        """
        self.logger.info(
            "The openEuler Hardware Compatibility Test Suite", log_print=False)
        copy_pci()
        self.load()
        certdevice = CertDevice(self.logger)

        while True:
            self.submit()

            if self.check_result():
                self.logger.info("All cases are passed, test end.")
                return True

            oec_devices = certdevice.get_devices()
            self.devices = DeviceDocument(CertEnv.devicefile, self.logger, oec_devices)
            self.devices.save()
            test_factory = self.get_tests(oec_devices)
            self.update_factory(test_factory)
            if not self.choose_tests():
                return True

            test_suite = create_test_suite(self.test_factory, self.logger)
            args = argparse.Namespace(
                test_factory=self.test_factory, test_suite=test_suite)
            job = Job(args)
            job.run()
            self.save(job)

    def run_rebootup(self):
        """
        rebootup
        :return:
        """
        try:
            if not os.path.exists(CertEnv.rebootfile):
                return True
            self.load()
            test_suite = create_test_suite(self.test_factory, self.logger)
            args = argparse.Namespace(
                test_factory=self.test_factory, test_suite=test_suite)
            job = Job(args)
            reboot = Reboot(None, job, None)
            if reboot.check(logger=self.logger):
                job = reboot.job
                job.run()
            reboot.clean()
            self.save(job)
            return True
        except Exception as e:
            self.logger.error("Run reboot up failed. %s" % e)
            return False

    def clean(self):
        """
        clean all compatibility test file
        :return:
        """
        if self.ui.prompt_confirm("Are you sure to clean all "
                                  "compatibility test data?"):
            if os.path.exists(CertEnv.certificationfile):
                os.remove(CertEnv.certificationfile)
            if os.path.exists(CertEnv.factoryfile):
                os.remove(CertEnv.factoryfile)
            if os.path.exists(CertEnv.devicefile):
                os.remove(CertEnv.devicefile)
        self.logger.info("Clean compatibility test data succeed.")
        return True

    def load(self):
        """
        load certification
        :return:
        """
        os.makedirs(os.path.dirname(CertEnv.datadirectory), exist_ok=True)
        if not self.certification:
            self.certification = CertDocument(
                CertEnv.certificationfile, self.logger)
            if not self.certification.document:
                self.certification.new()
                self.certification.save()
        if not self.test_factory:
            factory_doc = FactoryDocument(CertEnv.factoryfile, self.logger)
            self.test_factory = factory_doc.get_factory()

        oec_id = self.certification.get_certify()
        hardware_info = self.certification.get_hardware()
        self.client = Client(hardware_info, oec_id, self.logger)
        version = self.certification.get_oech_value("VERSION", "version")
        name = self.certification.get_oech_value("NAME", "client_name")
        self.certification.save()

        display_message = "    %s: ".ljust(20) % name + version + "\n" \
            "    Compatibility Test ID: ".ljust(30) + oec_id + "\n" \
            "    Hardware Info: ".ljust(30) + hardware_info + "\n" \
            "    Product URL: ".ljust(30) + self.certification.get_url() + "\n" \
            "    OS Info: ".ljust(30) + self.certification.get_os() + "\n" \
            "    Kernel Info: ".ljust(30) + self.certification.get_kernel() + "\n" \
            "    Test Server: ".ljust(30) + self.certification.get_server()
        self.logger.info(display_message, log_print=False)

    def save(self, job):
        """
        collect Job log
        :param job:
        :return:
        """
        doc_dir = os.path.join(CertEnv.logdirectoy, job.job_id)
        if not os.path.exists(doc_dir):
            return
        FactoryDocument(CertEnv.factoryfile, self.logger, self.test_factory).save()
        shutil.copy(CertEnv.certificationfile, doc_dir)
        shutil.copy(CertEnv.devicefile, doc_dir)
        shutil.copy(CertEnv.factoryfile, doc_dir)

        cwd = os.getcwd()
        os.chdir(os.path.dirname(doc_dir))
        self.dir_name = "oech-" + datetime.datetime.now().strftime("%Y%m%d%H%M%S") \
                        + "-" + job.job_id
        pack_name = self.dir_name + ".tar"
        os.rename(job.job_id, self.dir_name)
        
        cmd_result = self.command.run_cmd(
            "tar -cf %s --exclude '*.lock' %s" % (pack_name, self.dir_name), log_print=False)
        if cmd_result[2] != 0:
            self.logger.error("Collect job log failed.")
            return
        
        self.logger.info("Log saved to file: %s succeed." %
                         os.path.join(os.getcwd(), pack_name))
        shutil.copy(pack_name, CertEnv.datadirectory)
        for sublist in os.walk("./"):
            for dirname in sublist[1]:
                shutil.rmtree(dirname)
            break
        os.chdir(cwd)

    def submit(self):
        """
        submit last result
        :return:
        """
        packages = list()
        pattern = re.compile("^oech-[0-9]{14}-[0-9a-zA-Z]{10}.tar$")
        files = []
        for sublist in os.walk(CertEnv.datadirectory):
            files = sublist[2]
            break
        packages.extend(filter(pattern.search, files))
        if len(packages) == 0:
            return
        packages.sort()

        if self.ui.prompt_confirm("Do you want to submit last result?"):
            server = self.certification.get_server()
            path = os.path.join(CertEnv.datadirectory, packages[-1])
            if not self.upload(path, server):
                self.logger.error(
                    "Upload result to server %s failed." % server)
            else:
                self.logger.info(
                    "Upload result to server %s succeed." % server)
            time.sleep(2)

        for filename in packages:
            os.remove(os.path.join(CertEnv.datadirectory, filename))

    def upload(self, path, server):
        """
        uploaded result to server
        :param path:
        :param server:
        :return:
        """
        self.logger.info(
            "Start to upload result to server %s, please wait." % server, log_print=False)
        if not self.client:
            oec_id = self.certification.get_certify()
            hardware_info = self.certification.get_hardware()
            self.client = Client(hardware_info, oec_id, self.logger)
        return self.client.upload(path, server)

    def get_tests(self, devices):
        """
        get test items
        :param devices:
        :return:
        """
        sort_devices = self.sort_tests(devices)
        empty_device = Device(logger=self.logger)
        test_factory = list()
        casenames = []
        for (_, dirs, filenames) in os.walk(CertEnv.testdirectoy):
            dirs.sort()
            for filename in filenames:
                if filename.endswith(".py") and \
                        not filename.startswith("__init__"):
                    casenames.append(filename.split(".")[0])

        with open(CertEnv.pcifile) as file:
            for testname in casenames:
                if sort_devices.get(testname):
                    for device in sort_devices[testname]:
                        test = dict()
                        test["name"] = testname
                        test["device"] = device
                        test["run"] = True
                        test["status"] = "NotRun"
                        test["reboot"] = False
                        test["driverName"] = test.get("device", "").get_driver()
                        test["driverVersion"] = test.get("device", "").get_driver_version()
                        test["boardModel"], test["chipModel"] = test.get("device", "").get_model(testname, file)
                        test_factory.append(test)
                elif testname in NODEVICE:
                    test = dict()
                    test["name"] = testname
                    test["device"] = empty_device
                    test["run"] = True
                    test["status"] = "NotRun"
                    test["reboot"] = False
                    test_factory.append(test)
        return test_factory

    def sort_tests(self, devices):
        """
        sort tests
        :param devices:
        :return:
        """
        sort_devices = dict()
        empty_device = Device(logger=self.logger)
        for device in devices:
            if device.get_property("SUBSYSTEM") == "usb" and \
                    device.get_property("ID_VENDOR_FROM_DATABASE") == \
                    "Linux Foundation" and \
                    ("2." in device.get_property("ID_MODEL_FROM_DATABASE") or
                     "3." in device.get_property("ID_MODEL_FROM_DATABASE")):
                sort_devices["usb"] = [empty_device]
                continue
            if (device.get_property("DEVTYPE") == "disk" and
                not device.get_property("ID_TYPE")) or \
                    device.get_property("ID_TYPE") == "disk":
                if "nvme" in device.get_property("DEVPATH"):
                    sort_devices["disk"] = [empty_device]
                    if "nvme" in sort_devices.keys():
                        sort_devices["nvme"].extend([device])
                    else:
                        sort_devices["nvme"] = [device]
                elif "/host" in device.get_property("DEVPATH"):
                    sort_devices["disk"] = [empty_device]
            if "RAID" in device.get_property("ID_PCI_SUBCLASS_FROM_DATABASE") or \
                    ("SCSI" in device.get_property("ID_PCI_SUBCLASS_FROM_DATABASE") and
                     "HBA" not in device.get_property("ID_MODEL_FROM_DATABASE")):
                if "raid" in sort_devices.keys():
                    sort_devices["raid"].extend([device])
                else:
                    sort_devices["raid"] = [device]
                continue
            if "Fibre Channel" in device.get_property("ID_PCI_SUBCLASS_FROM_DATABASE"):
                if "fc" in sort_devices.keys():
                    sort_devices["fc"].extend([device])
                else:
                    sort_devices["fc"] = [device]
                continue
            driver = device.get_property("DRIVER")
            if any([d in driver for d in GPU_DRIVER]):
                if "gpu" in sort_devices.keys():
                    sort_devices["gpu"].extend([device])
                else:
                    sort_devices["gpu"] = [device]
                if driver == "nvidia":
                    if "vgpu" in sort_devices.keys():
                        sort_devices["vgpu"].extend([device])
                    else:
                        sort_devices["vgpu"] = [device]
                    continue
            if device.get_property("SUBSYSTEM") == "net" and \
                    device.get_property("INTERFACE"):
                interface = device.get_property("INTERFACE")
                cmd_result = self.command.run_cmd("nmcli device")
                for line in cmd_result[0].split("\n"):
                    if interface in line and IB in line:
                        if IB in sort_devices.keys():
                            sort_devices[IB].extend([device])
                        else:
                            sort_devices[IB] = [device]
                    elif interface in line and "ethernet" in line:
                        if "ethernet" in sort_devices.keys():
                            sort_devices["ethernet"].extend([device])
                        else:
                            sort_devices["ethernet"] = [device]
                    elif interface in line and "wifi" in line:
                        if "wlan" in sort_devices.keys():
                            sort_devices["wlan"].extend([device])
                        else:
                            sort_devices["wlan"] = [device]
                continue
            if device.get_property("ID_CDROM") == "1":
                for dev_type in CDTYPES:
                    if device.get_property("ID_CDROM_" + dev_type) == "1":
                        if "cdrom" in sort_devices.keys():
                            sort_devices["cdrom"].extend([device])
                        else:
                            sort_devices["cdrom"] = [device]
                        break
            if device.get_property("SUBSYSTEM") == "ipmi":
                sort_devices["ipmi"] = [empty_device]

            id_vendor = device.get_property("ID_VENDOR_FROM_DATABASE")
            if any([k in id_vendor for k in KEYCARD_VENDORS]):
                sort_devices["keycard"] = [device]
                continue
            
        cmd_result = self.command.run_cmd("dmidecode | grep 'IPMI Device Information'")
        if cmd_result[2] == 0:
            sort_devices["ipmi"] = [empty_device]

        return sort_devices

    def edit_tests(self):
        """
        edit test items
        :return:
        """
        while True:
            for test in self.test_factory:
                if test["name"] == "system":
                    test["run"] = True
                    if test["status"] == "PASS":
                        test["status"] = "Force"

            self.logger.info('\033c', log_print=False)
            self.logger.info("Select tests to run:", log_print=False)
            self.show_tests()
            reply = self.ui.prompt("Selection (<number>|all|none|quit|run): ")
            reply = reply.lower()
            if reply in ["r", "run"]:
                return True
            if reply in ["q", "quit"]:
                return False
            if reply in ["n", "none"]:
                for test in self.test_factory:
                    test["run"] = False
                continue
            if reply in ["a", "all"]:
                for test in self.test_factory:
                    test["run"] = True
                continue

            num_lst = reply.split(" ")
            for num in num_lst:
                try:
                    num = int(num)
                except ValueError:
                    continue

                if 0 < num <= len(self.test_factory):
                    self.test_factory[num - 1]["run"] = not \
                        self.test_factory[num - 1]["run"]
                    continue

    def show_tests(self):
        """
        show test items
        :return:
        """
        device_info = namedtuple('Device_info', DEVICE_INFO)
        self.logger.info("\033[1;35m" + "No.".ljust(4) + "Run-Now?".ljust(10)
                         + "status".ljust(10) + "Class".ljust(14) +
                         "device".capitalize().ljust(15)
                         + DRIVER.ljust(15) + VERSION.ljust(18) +
                         CHIP.ljust(20)
                         + "%s\033[0m" % BOARD, log_print=False)
        num = 0
        for test in self.test_factory:
            name = test["name"]
            if name == "system":
                test["run"] = True
                if test["status"] == "PASS":
                    test["status"] = "Force"

            status = test["status"]
            device = test["device"].get_name()
            board = test.get("boardModel", "")
            chip = test.get("chipModel", "")
            driver = test.get("driverName", "")
            version = test.get("driverVersion", "")
            run = "no"
            if test["run"] is True:
                run = "yes"
            num = num + 1
            if status == "PASS":
                color = "2"
            elif status == "FAIL":
                color = "1"
            elif status == "Force":
                color = "3"
            else:
                color = "4"
            device = device_info(color, status, num, run, name,
                                 device, driver, version, chip, board)
            self._print_tests(device)

    def choose_tests(self):
        """
        choose test behavior
        :return:
        """
        for test in self.test_factory:
            if test["status"] == "PASS":
                test["run"] = False
            else:
                test["run"] = True
        self.logger.info('\033c', log_print=False)
        self.logger.info("These tests are recommended to "
                         "complete the compatibility test: ", log_print=False)
        self.show_tests()
        action = self.ui.prompt("Ready to begin testing?",
                                ["run", "edit", "quit"])
        action = action.lower()
        if action in ["r", "run"]:
            return True
        if action in ["q", "quit"]:
            return False
        if action in ["e", "edit"]:
            return self.edit_tests()
        self.logger.info("Invalid choice!", log_print=False)
        return self.choose_tests()

    def check_result(self):
        """
        check test result
        :return:
        """
        if len(self.test_factory) == 0:
            return False
        for test in self.test_factory:
            if test["status"] != "PASS":
                return False
        return True

    def update_factory(self, test_factory):
        """
        update tese factory
        :param test_factory:
        :return:
        """
        if not self.test_factory:
            self.test_factory = test_factory
        else:
            for test in self.test_factory:
                if not search_factory(test, test_factory):
                    self.test_factory.remove(test)
                    self.logger.info("delete %s test %s" % (test["name"],
                                                            test["device"].get_name()))
            for test in test_factory:
                if not search_factory(test, self.test_factory):
                    self.test_factory.append(test)
                    self.logger.info("add %s test %s" % (test["name"],
                                                         test["device"].get_name()))
        self.test_factory.sort(key=lambda k: k["name"])
        FactoryDocument(CertEnv.factoryfile, self.logger, self.test_factory).save()

    def _print_tests(self, device):
        """
        print board information
        """
        self.logger.info("%-6d" % device.num + device.run.ljust(8)
                         + "\033[0;3%sm%s  \033[0m" % (device.color, device.status.ljust(8))
                         + device.name.ljust(14) + device.device.ljust(15) + device.driver.ljust(15)
                         + device.version.ljust(18) + device.chip.ljust(20) + device.board, log_print=False)
