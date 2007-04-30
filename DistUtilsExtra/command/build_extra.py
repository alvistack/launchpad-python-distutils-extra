#!/usr/bin/env python

import distutils
import glob
import os
import os.path
import re
import sys
import distutils.command.build
from build_l10n import build_l10n
from build_help import build_help
from build_icons import build_icons

class build_extra(distutils.command.build.build):
    def __init__(self, dist):
        distutils.command.build.build.__init__(self, dist)

        self.user_options.extend([("l10n", "l", "use the localsation"),
                                  ("icons", "i", "use icons"),
                                  ("help", "h", "use help system")])
        #FIXME: should be part of the distribution instance
        self.distribution.cmdclass["build_l10n"] = build_l10n
        self.distribution.cmdclass["build_help"] = build_icons
        self.distribution.cmdclass["build_icons"] = build_icons

    def initialize_options(self):
        distutils.command.build.build.initialize_options(self)
        self.l10n = False
        self.icons = False
        self.help = False

    def finalize_options(self):
        def has_help(command):
            #FIXME: should be part of the distribution instance
            return self.help == "True"
        def has_icons(command):
            #FIXME: should be part of the distribution instance
            return self.icons == "True"
        def has_l10n(command):
            #FIXME: should be part of the distribution instance
            return self.l10n == "True"
        distutils.command.build.build.finalize_options(self)
        self.sub_commands.append(("build_l10n", has_l10n))
        self.sub_commands.append(("build_icons", has_icons))
        self.sub_commands.append(("build_help", has_help))
