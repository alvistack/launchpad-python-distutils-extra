# DistUtilsExtra.command.check - check command for DistUtilsExtra
#
# Author: Rodney Dawes <rodney.dawes@canonical.com>
#
# Copyright 2009 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify it 
# under the terms of the GNU General Public License version 3, as published 
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but 
# WITHOUT ANY WARRANTY; without even the implied warranties of 
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR 
# PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along 
# with this program.  If not, see <http://www.gnu.org/licenses/>.

"""DistUtilsExtra.command.check

Implements the DistUtilsExtra 'check' command.
"""

import os
import subprocess

from distutils.core import Command


class check (Command):
    """Command to run lint and tests on a module."""

    description = "integrate pylint checks"

    user_options = [("config-file=", None,
                     "pylint config file to use"),
                    ("exclude-files=", None,
                     "list of files to exclude from lint checks"),
                    ("lint-files=", None,
                     "list of modules or packages to run lint checks on")
                   ]

    def initialize_options (self):
        self.config_file = None
        self.exclude_files = None
        self.lint_files = None

    def finalize_options (self):
        if self.config_file is None:
            self.config_file = ""
        if self.exclude_files is None:
            self.exclude_files = "[]"
        if self.lint_files is None:
            self.lint_files = "[" + self.__find_files() + "]"

    def run (self):
        config_file = ""
        if self.config_file:
            config_file = "--rcfile=" + self.config_file

        p = subprocess.Popen(["pylint", config_file] + eval(self.lint_files),
                             bufsize=4096, stdout=subprocess.PIPE)
        notices = p.stdout

        output = "".join(notices.readlines())
        if output != "":
            print "== Pylint notices =="
            print self.__group_lines_by_file(output)

    def __group_lines_by_file(self, input):
        """Format file:line:message output as lines grouped by file."""
        outputs = []
        filename = ""
        excludes = eval(self.exclude_files)
        for line in input.splitlines():
            current = line.split(":", 3)
            if line.startswith("    "):
                outputs.append("    " + current[0] + "")
            elif line.startswith("build/") or current[0] in excludes or \
                    len(current) < 3:
                pass
            elif filename == current[0]:
                outputs.append("    " + current[1] + ": " + current[2])
            elif filename != current[0]:
                filename = current[0]
                outputs.append("")
                outputs.append(filename + ":")
                outputs.append("    " + current[1] + ": " + current[2])

        return "\n".join(outputs)

    def __find_files(self):
        """Find all Python files under the current tree."""
        pyfiles = []
        for root, dirs, files in os.walk(os.getcwd(), topdown=False):
            for file in files:
                if file.endswith(".py"):
                    pyfiles.append("'" + os.path.join(root, file) + "'")
        pyfiles.sort()
        return ",".join(pyfiles)