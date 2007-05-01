#!/usr/bin/env python

import distutils
import glob
import os
import os.path
import re
import sys
import distutils.command.build

class build_extra(distutils.command.build.build):
    def __init__(self, dist):
        distutils.command.build.build.__init__(self, dist)

        self.user_options.extend([("l10n", None, "use the localsation"),
                                  ("icons", None, "use icons"),
                                  ("help", None, "use help system")])
    def initialize_options(self):
        distutils.command.build.build.initialize_options(self)
        self.l10n = False
        self.icons = False
        self.help = False

    def finalize_options(self):
        def has_help(command):
            return self.help == "True" or \
                   (self.distribution.cmdclass.has_key("build_help") and not \
                    self.help == "False")
        def has_icons(command):
            return self.icons == "True" or \
                   (self.distribution.cmdclass.has_key("build_icons") and not \
                    self.help == "False")
        def has_l10n(command):
            return self.l10n == "True" or \
                   (self.distribution.cmdclass.has_key("build_l10n") and not \
                    self.l10n == "False")
        distutils.command.build.build.finalize_options(self)
        self.sub_commands.append(("build_l10n", has_l10n))
        self.sub_commands.append(("build_icons", has_icons))
        self.sub_commands.append(("build_help", has_help))
