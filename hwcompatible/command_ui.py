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
    Provides methods for command-line interface interaction such as prompting the user for input,
    reading integers, getting confirmations, and editing values.
    """

    def __init__(self, echoResponses=False):
        """
        Initialize the CommandUI object with an option to echo responses.

        Args:
            echoResponses (bool, optional): Whether to echo the user's responses. Defaults to False.
        """
        self.echo = echoResponses

    @staticmethod
    def print_pipe(pipe):
        """
        Print data from the given pipe until there is no more data.

        Args:
            pipe (file-like object): A pipe-like object to read from.
        """
        while 1:
            line = pipe.readline()
            if line:
                sys.stdout.write(line)
            else:
                return pipe.close()

    def prompt(self, question, choices=None):
        """
        Prompt the user for input with an optional set of choices.

        Args:
            question (str): The question to ask the user.
            choices (list, optional): A list of possible choices. Defaults to None.

        Returns:
            str: The user's response stripped of leading/trailing whitespace.
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
        Prompt the user for an integer input with an optional set of choices.

        Args:
            question (str): The question to ask the user.
            choices (list, optional): A list of possible choices. Defaults to None.

        Returns:
            int: The user's response converted to an integer.
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
        Prompt the user for a yes/no confirmation.

        Args:
            question (str): The question to ask the user.

        Returns:
            bool: True if the user's response indicates 'yes', False otherwise.
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
        Prompt the user to edit a given value with an optional set of choices.

        Args:
            label (str): The label to display next to the input field.
            value (str): The initial value to be edited.
            choices (list, optional): A list of possible choices. Defaults to None.
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