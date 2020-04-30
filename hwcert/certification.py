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

import os
import time
import argparse
import shutil
import datetime
import re

from .document import CertDocument, DeviceDocument, FactoryDocument
from .env import CertEnv
from .device import CertDevice, Device
from .command import Command, CertCommandError
from .commandUI import CommandUI
from .job import Job
from .reboot import Reboot
from .client import Client


class EulerCertification():

    def __init__(self):
        self.certification = None
        self.test_factory = list()
        self.devices = None
        self.ui = CommandUI()
        self.client = None

    def run(self):
        print("The openEuler Hardware Certification Test Suite")
        self.load()
        certdevice = CertDevice()

        while True:
            self.submit()

            if self.check_result():
                print("All cases are passed, test end.")
                return True

            devices = certdevice.get_devices()
            self.devices = DeviceDocument(CertEnv.devicefile, devices)
            self.devices.save()

            # test_factory format example: [{"name":"nvme", "device":device, "run":True, "status":"PASS", "reboot":False}]
            test_factory = self.get_tests(devices)
            self.update_factory(test_factory)
            if not self.choose_tests():
                return True

            args = argparse.Namespace(test_factory=self.test_factory)
            job = Job(args)
            job.run()
            self.save(job)

    def run_rebootup(self):
        try:
            self.load()
            args = argparse.Namespace(test_factory=self.test_factory)
            job = Job(args)
            reboot = Reboot(None, job, None)
            if reboot.check():
                job.run()
            reboot.clean()
            self.save(job)
            return True
        except Exception as e:
            print(e)
            return False

    def clean(self):
        if self.ui.prompt_confirm("Are you sure to clean all certification data?"):
            try:
                Command("rm -rf %s" % CertEnv.certificationfile).run()
                Command("rm -rf %s" % CertEnv.factoryfile).run()
                Command("rm -rf %s" % CertEnv.devicefile).run()
            except Exception as e:
                print(e)
                return False
        return True

    def load(self):
        if not os.path.exists(CertEnv.datadirectory):
            os.mkdir(CertEnv.datadirectory)

        if not self.certification:
            self.certification = CertDocument(CertEnv.certificationfile)
            if not self.certification.document:
                self.certification.new()
                self.certification.save()
        if not self.test_factory:
            factory_doc = FactoryDocument(CertEnv.factoryfile)
            self.test_factory = factory_doc.get_factory()

        cert_id = self.certification.get_certify()
        hardware_info = self.certification.get_hardware()
        self.client = Client(hardware_info, cert_id)
        print("    Certification ID: ".ljust(30) + cert_id)
        print("    Hardware Info: ".ljust(30) + hardware_info)
        print("    Product URL: ".ljust(30) + self.certification.get_url())
        print("    OS Info: ".ljust(30) + self.certification.get_os())
        print("    Kernel Info: ".ljust(30) + self.certification.get_kernel())
        print("    Test Server: ".ljust(30) + self.certification.get_server())
        print("")

    def save(self, job):
        doc_dir = os.path.join(CertEnv.logdirectoy, job.job_id)
        if not os.path.exists(doc_dir):
            return
        FactoryDocument(CertEnv.factoryfile, self.test_factory).save()
        shutil.copy(CertEnv.certificationfile, doc_dir)
        shutil.copy(CertEnv.devicefile, doc_dir)
        shutil.copy(CertEnv.factoryfile, doc_dir)

        cwd = os.getcwd()
        os.chdir(os.path.dirname(doc_dir))
        dir_name = "eulercert-" + datetime.datetime.now().strftime("%Y%m%d%H%M%S") + "-" + job.job_id
        pack_name = dir_name +".tar"
        cmd = Command("tar -cf %s %s" % (pack_name, dir_name))
        try:
            os.rename(job.job_id, dir_name)
            cmd.run()
        except CertCommandError:
            print("Error:Job log collect failed.")
            return
        print("Log saved to %s succ." % os.path.join(os.getcwd(), pack_name))
        shutil.copy(pack_name, CertEnv.datadirectory)
        for (rootdir, dirs, filenams) in os.walk("./"):
            for dirname in dirs:
                shutil.rmtree(dirname)
            break
        os.chdir(cwd)

    def submit(self):
        packages = list()
        pattern = re.compile("^eulercert-[0-9]{14}-[0-9a-zA-Z]{10}.tar$")
        for (root, dirs, files) in os.walk(CertEnv.datadirectory):
            break
        packages.extend(filter(pattern.search, files))
        if len(packages) == 0:
            return
        packages.sort()

        if self.ui.prompt_confirm("Do you want to submit last result?"):
            server = self.certification.get_server()
            path = os.path.join(CertEnv.datadirectory, packages[-1])
            if not self.upload(path, server):
                print("Upload failed.")
            else:
                print("Successfully upload result to server %s." % server)
            time.sleep(2)

        for filename in packages:
            os.remove(os.path.join(CertEnv.datadirectory, filename))

    def upload(self, path, server):
        print("uploading...")
        if not self.client:
            cert_id = self.certification.get_certify()
            hardware_info = self.certification.get_hardware()
            self.client = Client(hardware_info, cert_id)
        return self.client.upload(path, server)

    def get_tests(self, devices):
        nodevice = ["cpufreq", "memory", "clock", "profiler", "system", "stress", "kdump", "perf", "acpi", "watchdog"]
        ethernet = ["ethernet"]
        infiniband = ["infiniband"]
        storage = ["nvme", "disk", "nvdimm"]
        cdrom = ["cdrom"]
        sort_devices = self.sort_tests(devices)
        empty_device = Device()
        test_factory = list()
        casenames = []
        for (dirpath, dirs, filenames) in os.walk(CertEnv.testdirectoy):
            dirs.sort()
            for filename in filenames:
                if filename.endswith(".py") and not filename.startswith("__init__"):
                    casenames.append(filename.split(".")[0])

        for testname in casenames:
            if sort_devices.get(testname):
                for device in sort_devices[testname]:
                    test = dict()
                    test["name"] = testname
                    test["device"] = device
                    test["run"] = True
                    test["status"] = "NotRun"
                    test["reboot"] = False
                    test_factory.append(test)
            elif testname in nodevice:
                test = dict()
                test["name"] = testname
                test["device"] = empty_device
                test["run"] = True
                test["status"] = "NotRun"
                test["reboot"] = False
                test_factory.append(test)
        return test_factory

    def sort_tests(self, devices):
        sort_devices = dict()
        empty_device = Device()
        for device in devices:
            if device.get_property("SUBSYSTEM") == "usb" and \
               device.get_property("ID_VENDOR_FROM_DATABASE") == "Linux Foundation" and \
               ("2." in device.get_property("ID_MODEL_FROM_DATABASE") or \
               "3." in device.get_property("ID_MODEL_FROM_DATABASE")):
                sort_devices["usb"] = [empty_device]
                continue
            if device.get_property("PCI_CLASS") == "30000" or device.get_property("PCI_CLASS") == "38000":
                sort_devices["video"] = [device]
                continue
            if device.get_property("SUBSYSTEM") == "tape" and "/dev/st" in device.get_property("DEVNAME"):
                try:
                    sort_devices["tape"].extend([device])
                except KeyError:
                    sort_devices["tape"] = [device]
                continue
            if (device.get_property("DEVTYPE") == "disk" and not device.get_property("ID_TYPE")) or \
               device.get_property("ID_TYPE") == "disk":
                if "nvme" in device.get_property("DEVPATH"):
                    sort_devices["disk"] = [empty_device]
                    try:
                        sort_devices["nvme"].extend([device])
                    except KeyError:
                        sort_devices["nvme"] = [device]
                    continue
                elif "/host" in device.get_property("DEVPATH"):
                    sort_devices["disk"] = [empty_device]
                continue
            if device.get_property("SUBSYSTEM") == "net" and device.get_property("INTERFACE"):
                interface = device.get_property("INTERFACE")
                nmcli = Command("nmcli device")
                nmcli.start()
                while True:
                    line = nmcli.readline()
                    if line:
                        if interface in line and "infiniband" in line:
                            try:
                                sort_devices["infiniband"].extend([device])
                            except KeyError:
                                sort_devices["infiniband"] = [device]
                        elif interface in line and "ethernet" in line:
                            try:
                                sort_devices["ethernet"].extend([device])
                            except KeyError:
                                sort_devices["ethernet"] = [device]
                        elif interface in line and "wifi" in line:
                            try:
                                sort_devices["wlan"].extend([device])
                            except KeyError:
                                sort_devices["wlan"] = [device]
                    else:
                        break
                continue
            if device.get_property("ID_CDROM") == "1":
                types = ["DVD_RW", "DVD_PLUS_RW", "DVD_R", "DVD_PLUS_R", "DVD", \
                         "BD_RE",  "BD_R", "BD", "CD_RW", "CD_R", "CD"]
                for type in types:
                    if device.get_property("ID_CDROM_" + type) == "1":
                        try:
                            sort_devices["cdrom"].extend([device])
                        except KeyError:
                            sort_devices["cdrom"] = [device]
                        break
            if device.get_property("SUBSYSTEM") == "ipmi":
                sort_devices["ipmi"] = [empty_device]
        try:
            Command("dmidecode").get_str("IPMI Device Information", single_line=False)
            sort_devices["ipmi"] = [empty_device]
        except:
            pass

        return sort_devices

    def edit_tests(self):
        while True:
            for test in self.test_factory:
                if test["name"] == "system":
                    test["run"] = True
                    if test["status"] == "PASS":
                        test["status"] = "Force"

            os.system("clear")
            print("Select tests to run:")
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

            try:
                num = int(reply)
            except:
                continue

            if num > 0 and num <= len(self.test_factory):
                self.test_factory[num-1]["run"] = not self.test_factory[num-1]["run"]
                continue

    def show_tests(self):
        print("\033[1;35m" + "No.".ljust(4)  + "Run-Now?".ljust(10) \
              + "Status".ljust(8) + "Class".ljust(14) + "Device\033[0m")
        num = 0
        for test in self.test_factory:
            name = test["name"]
            if name == "system":
                test["run"] = True
                if test["status"] == "PASS":
                    test["status"] = "Force"

            status = test["status"]
            device = test["device"].get_name()
            run = "no"
            if test["run"] == True:
                run = "yes"

            num = num + 1
            if status == "PASS":
                print("%-6d"%num + run.ljust(8) + "\033[0;32mPASS    \033[0m" \
                      + name.ljust(14) + "%s"%device)
            elif status == "FAIL":
                print("%-6d"%num + run.ljust(8) + "\033[0;31mFAIL    \033[0m" \
                      + name.ljust(14) + "%s"%device)
            elif status == "Force":
                print("%-6d"%num + run.ljust(8) + "\033[0;33mForce   \033[0m" \
                      + name.ljust(14) + "%s"%device)
            else:
                print("%-6d"%num + run.ljust(8) + "\033[0;34mNotRun  \033[0m" \
                      + name.ljust(14) + "%s"%device)

    def choose_tests(self):
        for test in self.test_factory:
            if test["status"] == "PASS":
                test["run"] = False
            else:
                test["run"] = True
        os.system("clear")
        print("These tests are recommended to complete the certification:")
        self.show_tests()
        action = self.ui.prompt("Ready to begin testing?", ["run", "edit", "quit"])
        action = action.lower()
        if action in ["r", "run"]:
            return True
        elif action in ["q", "quit"]:
            return False
        elif action in ["e", "edit"]:
            return self.edit_tests()
        else:
            print("Invalid choice!")
            return self.choose_tests()

    def check_result(self):
        if len(self.test_factory) == 0:
            return False
        for test in self.test_factory:
            if test["status"] != "PASS":
                return False
        return True

    def update_factory(self, test_factory):
        if not self.test_factory:
            self.test_factory = test_factory
        else:
            factory_changed = False
            for test in self.test_factory:
                if not self.search_factory(test, test_factory):
                    self.test_factory.remove(test)
                    print("delete %s test %s" % (test["name"], test["device"].get_name()))
            for test in test_factory:
                if not self.search_factory(test, self.test_factory):
                    self.test_factory.append(test)
                    print("add %s test %s" % (test["name"], test["device"].get_name()))
        self.test_factory.sort(key=lambda k: k["name"])
        FactoryDocument(CertEnv.factoryfile, self.test_factory).save()

    def search_factory(self, obj_test, test_factory):
        for test in test_factory:
            if test["name"] == obj_test["name"] and test["device"].path == obj_test["device"].path:
                return True
        return False
