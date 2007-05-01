"""distutils_extra.command.build_icons

Implement DistutilsExtra's 'build_icons' command.
"""

# Created by Sebastian Heinlein 

__revision__ = "$Id$"

import distutils
import glob
import os
import os.path
import re
import sys
import distutils.command.build

class build_icons(distutils.cmd.Command):

    description = "select all icons for installation"

    user_options= [('icon_dir', None, 'icon directory of the source tree')]

    def initialize_options(self):
        self.icon_dir = None

    def finalize_options(self):
        if self.icon_dir is None:
            self.icon_dir = os.path.join("data","icons")

    def run(self):
        data_files = self.distribution.data_files

        for size in glob.glob(os.path.join(self.icon_dir, "*")):
            for category in glob.glob(os.path.join(size, "*")):
                icons = []
                for icon in glob.glob(os.path.join(category,"*")):
                    icons.append(icon)
                    data_files.append(("share/icons/hicolor/%s/%s" % \
                                       (os.path.basename(size), \
                                        os.path.basename(category)), \
                                        icons))
# class build
