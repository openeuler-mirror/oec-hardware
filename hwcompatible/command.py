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

import sys
import re
import subprocess


class Command:

    def __init__(self, command):
        """ Creates a Command object that wraps the shell command """
        self.command = command
        self.origin_output = None
        self.output = None
        self.errors = None
        self.returncode = 0
        self.pipe = None
        self.regex = None
        self.single_line = True
        self.regex_group = None

    def _run(self):
        if sys.version_info.major < 3:
            self.pipe = subprocess.Popen(self.command, shell=True,
                                         stdin=subprocess.PIPE,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)
        else:
            self.pipe = subprocess.Popen(self.command, shell=True,
                                         stdin=subprocess.PIPE,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE,
                                         encoding='utf8')
        (output, errors) = self.pipe.communicate()
        if output:
            #Strip new line character/s if any from the end of output string
            output = output.rstrip('\n')
            self.origin_output = output
            self.output = output.splitlines()
        if errors:
            self.errors = errors.splitlines()
        self.returncode = self.pipe.returncode

    def start(self):
        if sys.version_info.major < 3:
            self.pipe = subprocess.Popen(self.command, shell=True,
                                         stdin=subprocess.PIPE,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)
        else:
            self.pipe = subprocess.Popen(self.command, shell=True,
                                         stdin=subprocess.PIPE,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE,
                                         encoding='utf8')

    def run(self, ignore_errors=False):
        """ run the command
            ignore_errors: do not raise exceptions
        """
        self._run()
        if not ignore_errors:
            if self.returncode != 0:
                self.print_output()
                self.print_errors()
                raise CertCommandError(self, "returned %d" % self.returncode)

            if self.errors and len(self.errors) > 0:
                self.print_errors()
            #     raise CertCommandError(self, "has output on stderr")

    def run_quiet(self):
        self._run()
        if self.returncode != 0:
            raise CertCommandError(self, "returned %d" % self.returncode)

    def echo(self, ignore_errors=False):
        self.run(ignore_errors)
        self.print_output()
        return

    def print_output(self):
        if self.output:
            for line in self.output:
                sys.stdout.write( line )
                sys.stdout.write("\n")
            sys.stdout.flush()

    def print_errors(self):
        if self.errors:
            for line in self.errors:
                sys.stderr.write( line )
                sys.stderr.write("\n")
            sys.stderr.flush()

    def pid(self):
        if self.pipe:
            return self.pipe.pid

    def readline(self):
        if self.pipe:
            return self.pipe.stdout.readline()

    def read(self):
        self.pipe = subprocess.Popen(self.command, shell=True,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT)
        if self.pipe:
            return self.pipe.stdout.read().decode('utf-8', 'ignore').rstrip()

    def poll(self):
        if self.pipe:
            return self.pipe.poll()

    def _get_str(self, regex=None, regex_group=None, single_line=True, return_list=False, ignore_errors=False):
        self.regex = regex
        self.single_line = single_line
        self.regex_group = regex_group

        self._run()

        if self.single_line:
            if self.output and len(self.output) > 1:
                raise CertCommandError(self, "Found %u lines of output, expected 1" % len(self.output))

            if self.output:
                line = self.output[0].strip()
                if not self.regex:
                    return line
                # otherwise, try the regex
                pattern = re.compile(self.regex)
                match = pattern.match(line)
                if match:
                    if self.regex_group:
                        return match.group(self.regex_group)
                    # otherwise, no group, return the whole line
                    return line

                # no regex match try a grep-style match
                if not self.regex_group:
                    match = pattern.search(line)
                    if match:
                        return match.group()

            # otherwise
            raise CertCommandError(self, "no match for regular expression %s" % self.regex)

        #otherwise, multi-line or single-line regex
        if not self.regex:
            raise CertCommandError(self, "no regular expression set for multi-line command")
        pattern = re.compile(self.regex)
        result = None
        if return_list:
            result = list()
        if self.output:
            for line in self.output:
                if self.regex_group:
                    match = pattern.match(line)
                    if match:
                        if self.regex_group:
                            if return_list:
                                result.append(match.group(self.regex_group))
                            else:
                                return match.group(self.regex_group)
                else:
                    # otherwise, return the matching line
                    match = pattern.search(line)
                    if match:
                        if return_list:
                            result.append(match.group())
                        else:
                            return match.group()
            if result:
                return result

        raise CertCommandError(self, "no match for regular expression %s" % self.regex)

    def get_str(self, regex=None, regex_group=None, single_line=True, return_list=False, ignore_errors=False):
        result = self._get_str(regex, regex_group, single_line, return_list)
        if not ignore_errors:
            if self.returncode != 0:
                self.print_output()
                self.print_errors()
                raise CertCommandError(self, "returned %d" % self.returncode)

            # if self.errors and len(self.errors) > 0:
            #     raise CertCommandError(self, "has output on stderr")

        return result


class CertCommandError(Exception):
    def __init__(self, command, message):
        self.message = message
        self.command = command

    def __str__(self):
        return "\"%s\" %s" % (self.command.command, self.message)

    def _get_message(self): return self.__message
    def _set_message(self, value): self.__message = value
    message = property(_get_message, _set_message)

