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
import shlex
import signal
import subprocess
import threading
import time
from typing import TYPE_CHECKING, List, Optional, Tuple
from .constants import SHELL_ENV

if TYPE_CHECKING:
    from .log import Logger


class Command:
    """ 
    Creates a Command object that wraps the shell command.

    Attributes:
        logger (Logger): A logging object used to record logs.
    """

    def __init__(self, logger: "Logger"):
        self.logger: "Logger" = logger

    @staticmethod
    def _stream_for_log(stream: str) -> str:
        """Return an explicit value for an empty command output stream."""
        return stream if stream else "<empty>"

    @staticmethod
    def _kill_processes(pipes) -> None:
        """Kill every process started for a command or pipeline."""
        for pipe in pipes:
            if pipe.poll() is not None:
                continue
            try:
                if os.name == "posix":
                    os.killpg(pipe.pid, signal.SIGKILL)
                else:
                    pipe.kill()
            except OSError:
                pass

    def _log_command_result(
        self,
        command: str,
        output: str,
        error: str,
        returncode: int,
        status: str,
        ignore_errors: bool,
        log_print: bool,
        terminal_print: bool,
        exception: Optional[Exception] = None,
    ) -> None:
        """Record both output streams for every command result."""
        exception_message = ""
        if exception is not None:
            exception_message = "\nException:\n%s" % exception
        message = (
            "Execute command %s %s.\n"
            "Return code: %s\n"
            "stdout:\n%s\n"
            "stderr:\n%s%s"
            % (command, status, returncode,
               self._stream_for_log(output),
               self._stream_for_log(error), exception_message))

        if status == "succeed" or (status == "failed" and ignore_errors):
            self.logger.info(message, log_print, terminal_print)
        else:
            self.logger.error(message, log_print, terminal_print)

    def run_cmd(
        self,
        command: str,
        ignore_errors: bool = False,
        log_print: bool = True,
        terminal_print: bool = False,
        timeout: Optional[float] = None,
    ) -> Tuple[str, str, int]:
        """
        Run single or multiple shell command

        The return code, stdout, and stderr are recorded for every outcome
        when log output is enabled. Empty streams are recorded as ``<empty>``.

        Args:
            command (string): Actual execution command
            ignore_errors (bool, optional): Log a nonzero result at INFO level
                so the caller can handle it. Defaults to False.
            log_print (bool, optional): Use for print messages into log file. Defaults to True.
            terminal_print (bool, optional): Use for print messages into terminal. Defaults to False.
            timeout (number, optional): Determine command execution timeout. Defaults to None.

        Returns:
            tuple: (output, error, returncode)
        """
        output = ""
        error = ""
        returncode = 1
        pipes = []
        stderr_outputs = []
        stderr_threads = []
        timed_out = False
        cur_env = os.environ.copy()
        try:
            cmd_list = self.change_command_format(
                command,
                log_print=log_print,
                terminal_print=terminal_print)
            for index, cmd in enumerate(cmd_list):
                if index == 0:
                    pipe = subprocess.Popen(cmd, universal_newlines=True, stderr=subprocess.PIPE,
                        stdout=subprocess.PIPE, start_new_session=True, env=(cur_env | SHELL_ENV))
                else:
                    pipe_stdout = pipes[-1].stdout
                    pipe = subprocess.Popen(cmd, stdin=pipe_stdout, universal_newlines=True, stderr=subprocess.PIPE,
                        stdout=subprocess.PIPE, start_new_session=True, env=(cur_env | SHELL_ENV))
                    pipe_stdout.close()
                pipes.append(pipe)

            stderr_outputs = [""] * len(pipes)

            def read_stderr(index, stream):
                try:
                    stderr_outputs[index] = stream.read()
                except (OSError, ValueError) as exception:
                    stderr_outputs[index] = (
                        "Unable to read pipeline stderr: %s" % exception)

            for index, pipe in enumerate(pipes[:-1]):
                thread = threading.Thread(
                    target=read_stderr,
                    args=(index, pipe.stderr),
                    daemon=True)
                thread.start()
                stderr_threads.append(thread)

            deadline = None if timeout is None else time.monotonic() + timeout

            def remaining_timeout():
                if deadline is None:
                    return None
                return max(0, deadline - time.monotonic())

            try:
                output, stderr_outputs[-1] = pipes[-1].communicate(
                    timeout=remaining_timeout())
                for pipe in pipes[:-1]:
                    pipe.wait(timeout=remaining_timeout())
            except subprocess.TimeoutExpired:
                timed_out = True
                self._kill_processes(pipes)
                output, stderr_outputs[-1] = pipes[-1].communicate()
                for pipe in pipes[:-1]:
                    pipe.wait()

            for thread in stderr_threads:
                thread.join()

            if len(stderr_outputs) == 1:
                error = stderr_outputs[0]
            else:
                error = "\n".join(
                    "[pipeline stage %d stderr]\n%s" % (index + 1, value)
                    for index, value in enumerate(stderr_outputs)
                    if value)
            returncode = pipes[-1].returncode

            if timed_out:
                self._log_command_result(
                    command, output, error, returncode, "timed out",
                    ignore_errors, log_print, terminal_print)
            elif returncode != 0:
                self._log_command_result(
                    command, output, error, returncode, "failed",
                    ignore_errors, log_print, terminal_print)
            else:
                self._log_command_result(
                    command, output, error, returncode, "succeed",
                    ignore_errors, log_print, terminal_print)
        except Exception as e:
            self._kill_processes(pipes)
            self._log_command_result(
                command, output, error, returncode, "failed",
                ignore_errors, log_print, terminal_print, exception=e)
        return output, error, returncode

    def change_command_format(
        self,
        command: str,
        log_print: bool = True,
        terminal_print: bool = False,
    ) -> List[List[str]]:
        """
        Change command format from string to list
        Args:
            command (string): Actual execution command
            log_print (bool, optional): Use for print messages into log file. Defaults to True.
            terminal_print (bool, optional): Use for print messages into terminal. Defaults to False.

        Returns:
            list: result
        """
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
