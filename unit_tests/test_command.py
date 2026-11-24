# Copyright (c) 2026 renwofei423
# oec-hardware is licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.

"""Offline regression tests for command argument and pipeline parsing."""

import shlex
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from hwcompatible.command import Command


class CommandParsingTest(unittest.TestCase):
    def setUp(self):
        self.command = Command(Mock())

    def test_literal_pipes(self):
        for argument in ["'a|b'", '\"a|b\"', r"a\|b", "'|'", "'a'\"|\"b"]:
            with self.subTest(argument=argument):
                expected = "|" if argument == "'|'" else "a|b"
                self.assertEqual(
                    self.command.run_cmd("printf %s " + argument, timeout=2),
                    (expected, "", 0))

    def test_regex_alternation_in_pipeline(self):
        self.assertEqual(
            self.command.run_cmd(
                "printf 'alpha\\nbeta\\ngamma\\n'|grep -E 'alpha|beta'", timeout=2),
            ("alpha\nbeta\n", "", 0))

    def test_quoted_filename(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report|result.txt"
            path.write_text("result\n")
            self.assertEqual(
                self.command.run_cmd("cat " + shlex.quote(str(path)), timeout=2),
                ("result\n", "", 0))

    def test_existing_pipeline(self):
        self.assertEqual(
            self.command.run_cmd("printf 'alpha\\nbeta\\n'|grep beta|wc -l", timeout=2),
            ("1\n", "", 0))

    def test_quoting_boundaries(self):
        for argument in [r"'a\'", r'"a\\"', r'"a\\\"|b"', "''", "'a # b'", r"a\ b"]:
            with self.subTest(argument=argument):
                self.assertEqual(
                    self.command.change_command_format("printf %s " + argument + "|cat"),
                    [["printf", "%s", *shlex.split(argument)], ["cat"]])

    def test_invalid_quoting(self):
        for command in ["printf 'unfinished|cat", "printf trailing" + chr(92)]:
            with self.subTest(command=command):
                with self.assertRaises(ValueError):
                    self.command.change_command_format(command)


if __name__ == "__main__":
    unittest.main()
