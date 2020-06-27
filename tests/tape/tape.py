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

import argparse

from hwcompatible.test import Test
from hwcompatible.command import Command, CertCommandError


class TapeTest(Test):
    """
    Tape test
    """
    def setup(self, args=None):
        """
        Initialization before test
        :param args:
        :return:
        """
        self.args = args or argparse.Namespace()
        self.device = getattr(args, "device", None)
        self.tapeDevice = self.device.get_property("DEVNAME")
        if self.tapeDevice == "":
            print("Did not found any Tape Device")
        else:
            print("Found the Tape Device :\n %s" % self.tapeDevice)

    def test(self):
        """
        test case
        :return:
        """
        if not self.tapeDevice:
            return False

        print("Testing tape device %s" % self.tapeDevice)
        # set default block size to 32k (64 x 512byte = 32k)
        bs = 64
        # rewind the tape
        try:
            tape_rewind = Command("mt -f %s rewind 2>/dev/null" % self.tapeDevice).read()
            print("Rewind tape : \n %s" % tape_rewind)
        except CertCommandError as exception:
            print(exception)
            return False
        # Write data
        try:
            tapewritedata = Command("tar -Pcb %s -f %s /usr" % (bs, self.tapeDevice)).read()
            if tapewritedata == 0:
                print("Write data done. Start comparing ...")
                # Compare data
                comparedata = Command("tar -Pdb %s -f %s /usr" % (bs, self.tapeDevice)).read()
                if comparedata == 0:
                    print("Tape test on device %s passed." % self.tapeDevice)
                    return True
                else:
                    print("Error: data comparison fail.")
                    return False
            else:
                print("Error: write data fail.")
                return False

        except CertCommandError as exception:
            print(exception)
            return False


if __name__ == "__main__":
    main = TapeTest()
    main.test()
