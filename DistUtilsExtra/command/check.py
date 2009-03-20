"""DistUtilsExtra.command.check

Implements the DistUtilsExtra 'check' command.
"""

import os
import re
import subprocess

from distutils.core import Command


class check (Command):
    """Command to run lint and tests on a module."""

    description = "integrate pylint checks"

    user_options = [('config-file=', None,
                     "pylint config file to use"),
                    ('exlcude-files=', None,
                     'list of files to exclude from lint checks'),
                    ('lint-files=', None,
                     'list of mdoules or packages to run lint checks on')
                   ]

    def initialize_options (self):
        self.config_file = None
        self.exclude_files = None
        self.lint_files = None

    def finalize_options (self):
        if self.config_file is None:
            self.config_file = ""
        if self.exclude_files is None:
            self.exclude_files = ""
        if self.lint_files is None:
            self.lint_files = "[" + self.__find_files() + "]"

    def run (self):
        config_file = ""
        if self.config_file:
            config_file = "--rcfile=" + self.config_file

        p = subprocess.Popen(["pylint", config_file] + eval(self.lint_files),
                             bufsize=4096, stdout=subprocess.PIPE)
        notices = p.stdout

        r = re.compile("""(^$|Unused import (action|_python)|
Unable to import .*sql(object|base)|
_action.* Undefined variable|
_getByName.* Instance|
Redefining built-in .id|
Redefining built-in 'filter'|
<lambda>] Using variable .* before assignment|
Comma not followed by a space/{N;N};/,[])}]|
Undefined variable.*valida|
ENABLED|
BYUSER)
""")
        lines = []
        for line in notices.readlines():
            lines.append(r.sub("", line))

        output = "".join(lines)
        if output != "":
            print "== Pylint notices =="
            print self.__group_lines_by_file(output)

    def __group_lines_by_file(self, input):
        """Format file:line:message output as lines grouped by file."""
        outputs = []
        filename = ""
        ignores = eval(self.exclude_files)
        for line in input.splitlines():
            current = line.split(':', 3)
            if line.startswith("    "):
                outputs.append("    " + current[0] + "")
            elif line.startswith("build/") or current[0] in ignores:
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
                if file.endswith('.py'):
                    pyfiles.append("'" + os.path.join(root, file) + "'")
        pyfiles.sort()
        return ",".join(pyfiles)
