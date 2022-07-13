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

import sys
import readline
from builtins import input
from .constants import SAMEASYES, YES, SAMEASNO, NO


class CommandUI:
    """
    Command user interface selection
    """

    def __init__(self, echoResponses=False):
        self.echo = echoResponses

    @staticmethod
    def print_pipe(pipe):
        """
        print pipe data
        :param pipe:
        :return:
        """
        while 1:
            line = pipe.readline()
            if line:
                sys.stdout.write(line)
            else:
                return pipe.close()

    def prompt(self, question, choices=None):
        """
        choice test item
        :param question:
        :param choices:
        :return:
        """
        while True:
            sys.stdout.write(question)
            if choices:
                sys.stdout.write(" (")
                sys.stdout.write("|".join(choices))
                sys.stdout.write(") ")
            sys.stdout.flush()
            reply = sys.stdin.readline()
            if reply.strip() and self.echo:
                sys.stdout.write("reply: %s" % reply)
            if not choices or reply.strip():
                return reply.strip()
            sys.stdout.write("Please enter a choice\n")

    def prompt_integer(self, question, choices=None):
        """
        choice test item
        :param question:
        :param choices:
        :return:
        """
        while True:
            sys.stdout.write(question)
            if choices:
                sys.stdout.write(" (")
                sys.stdout.write("|".join(choices))
                sys.stdout.write(") ")
            sys.stdout.flush()
            reply = sys.stdin.readline()
            try:
                value = int(reply.strip())
                if self.echo:
                    sys.stdout.write("reply: %u\n" % value)
                return value
            except ValueError:
                sys.stdout.write("Please enter an integer.\n")

    def prompt_confirm(self, question):
        """
        Command interface displays confirmation information
        :param question:
        :return:
        """
        while True:
            reply = self.prompt(question, (YES, NO))
            if reply.lower() in SAMEASYES:
                return True
            if reply.lower() in SAMEASNO:
                return False
            sys.stdout.write("Please reply %s or %s.\n" % (YES, NO))

    @staticmethod
    def prompt_edit(label, value, choices=None):
        """
        prompt choice edit
        :param label:
        :param value:
        :param choices:
        :return:
        """
        if not value:
            value = ""
        if choices:
            label += " ("
            label += "|".join(choices)
            label += ") "
        while True:
            readline.set_startup_hook(lambda: readline.insert_text(value))

            try:
                reply = input(label).strip()
                if not choices or reply in choices:
                    return reply
                sys.stdout.write(
                    "Please enter one of the following: %s" % " | ".join(choices))
            finally:
                readline.set_startup_hook()