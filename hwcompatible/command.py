#!/usr/bin/env python3
# coding: utf-8

# Copyright (c) 2020-2022 Huawei Technologies Co., Ltd.
# oec-hardware is licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may ob tain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Create: 2020-04-01

import os
from signal import signal
import subprocess
import shlex
from .constants import SHELL_ENV


class Command:
    """ 
    Creates a Command object that wraps the shell command 
    """

    def __init__(self, logger):
        self.logger = logger

    def run_cmd(self, command, ignore_errors=False, log_print=True, terminal_print=False, timeout=None):
        cmd_list = self.change_command_format(
            command, log_print=log_print, terminal_print=terminal_print)
        output = ""
        error = ""
        returncode = 1
        pipes = []
        try:
            for index, cmd in enumerate(cmd_list):
                if index == 0:
                    pipe = subprocess.Popen(cmd, universal_newlines=True, stderr=subprocess.PIPE,
                                            stdout=subprocess.PIPE, start_new_session=True, env=SHELL_ENV)
                else:
                    pipe_stdout = pipes[-1].stdout
                    pipe = subprocess.Popen(cmd, stdin=pipe_stdout, universal_newlines=True, stderr=subprocess.PIPE,
                                            stdout=subprocess.PIPE, start_new_session=True, env=SHELL_ENV)
                pipes.append(pipe)

            output, error = pipes[-1].communicate(timeout=timeout)
            returncode = pipes[-1].returncode
            if returncode == 0 and len(error) == 0:
                self.logger.info(
                    "Execute command %s succeed.\n %s" % (command, output), log_print, terminal_print)

            if returncode != 0 and len(error) != 0 and not ignore_errors:
                error = error.replace("\n", "").replace("\r", "")
                self.logger.error(
                    "Execute command %s failed.\n %s" % (command, error), log_print, terminal_print)
        except subprocess.TimeoutExpired:
            pipe.kill()
            pipe.terminate()
            os.killpg(pipe.pid, signal.SIGTERM)
            self.logger.error("Execute command timeout: %s." % command)
        except Exception as e:
            if not ignore_errors:
                self.logger.error(
                    "Execute command %s failed.\n %s" % (command, e), log_print, terminal_print)
        return [output, error, returncode]

    def change_command_format(self, command, log_print=True, terminal_print=False):
        cmd_list = []
        result = []
        self.logger.info("The command is: %s." %
                         command, log_print, terminal_print)

        if '|' in command:
            cmd_list = command.split("|")
        else:
            cmd_list.append(command)

        for cmd in cmd_list:
            cmd = shlex.split(cmd)
            result.append(cmd)

        return result
