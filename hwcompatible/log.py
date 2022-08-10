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
import sys
import datetime
import logging
from concurrent_log_handler import ConcurrentRotatingFileHandler
from .env import CertEnv
from .constants import MAX_BYTES, MAX_COUNT


class Logger():
    """
    Log management
    """

    def __init__(self, logname, logdir, out, err):
        self.logdir = None
        self.log = None
        self.stdout = out
        self.stderr = err
        self._check_logdir(logdir)
        self.logfile = os.path.join(self.logdir, logname)

    def start(self):
        """
        Start outputing to file
        :return:
        """
        self.log = logging.getLogger(name=self.logfile)
        formatter = logging.Formatter(
            '[%(asctime)s][%(levelname)s] %(message)s')
        file_handler = ConcurrentRotatingFileHandler(filename=self.logfile,
                                                     mode='a+',
                                                     encoding='utf-8',
                                                     maxBytes=MAX_BYTES,
                                                     backupCount=MAX_COUNT,
                                                     use_gzip=True)
        file_handler.setFormatter(formatter)
        self.log.addHandler(file_handler)

    def info(self, message, log_print=True, terminal_print=True):
        self._print(logging.INFO, message, log_print, terminal_print)

    def error(self, message, log_print=True, terminal_print=True):
        self._print(logging.ERROR, message, log_print, terminal_print)

    def warning(self, message, log_print=True, terminal_print=True):
        self._print(logging.WARNING, message, log_print, terminal_print)

    def stop(self):
        """
        Stop outputing to file
        :return:
        """
        self.stdout = sys.stdout
        self.stderr = sys.stderr

    def _check_logdir(self, logdir):
        """
        Check and create log directory
        """
        self.logdir = logdir
        if not self.logdir:
            curtime = datetime.datetime.now().isoformat()
            self.logdir = os.path.join(CertEnv.logdirectoy, curtime)
        if not logdir.startswith(os.path.sep):
            self.logdir = os.path.join(CertEnv.logdirectoy, self.logdir)
        if not os.path.exists(self.logdir):
            os.makedirs(self.logdir)

    def _print(self, level, message, log_print, terminal_print):
        """
        Print messages
        : param :
        : level : log level
        : message: the write message
        : log_print: set 'True' will write message to log file
        : terminal_print: set 'True' will write message to terminal
        """
        if log_print:
            self.log.setLevel(level)
            if level == logging.INFO:
                self.log.info(message)
            elif level == logging.ERROR:
                self.log.error(message)
            elif level == logging.WARNING:
                self.log.warning(message)

        if terminal_print:
            self.stdout.write(message)
            self.stdout.write("\n")
