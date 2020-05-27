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
import sys
import datetime

from .env import CertEnv


class Log(object):

    def __init__(self, logname='oech.log', logdir='__temp__'):
        if not logdir:
            curtime = datetime.datetime.now().isoformat()
            logdir = os.path.join(CertEnv.logdirectoy, curtime)
        if not logdir.startswith(os.path.sep):
            logdir = os.path.join(CertEnv.logdirectoy, logdir)
        if not os.path.exists(logdir):
            os.makedirs(logdir)

        self.dir = logdir
        logfile = os.path.join(logdir, logname)
        sys.stdout.flush()
        self.terminal = sys.stdout
        self.log = open(logfile, "a+")

    def write(self, message):
        self.terminal.write(message)
        if self.log:
            self.log.write(message)

    def flush(self):
        self.terminal.flush()
        if self.log:
            self.log.flush()

    def close(self):
        self.log.close()
        self.log = None

class Logger():
    def __init__(self, logname, logdir, out, err):
        self.log = Log(logname, logdir)
        self.stdout = out
        self.stderr = err

    def start(self):
        sys.stdout = self.log
        sys.stderr = sys.stdout

    def stop(self):
        sys.stdout.close()
        sys.stdout = self.stdout
        sys.stderr = self.stderr

