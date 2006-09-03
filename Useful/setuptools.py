#!/usr/bin/env python

import distutils
import glob
import os
import os.path
import re
import sys

class build_help(distutils.cmd.Command):
    def run(self):
        data_files = self.distribution.data_files
        print "Setting up help files..."
        for filepath in glob.glob("help/*"):
            lang = filepath[len("help/"):]
            print " Language: %s" % lang
            path_xml = os.path.join("share/gnome/help/gnome-app-install/",
                                    lang)
            path_figures = os.path.join("share/gnome/help/gnome-app-install/",
                                        lang, "figures")
            data_files.append((path_xml, (glob.glob("%s/*.xml" % filepath))))
            data_files.append((path_figures,
                               (glob.glob("%s/figures/*.png" % filepath))))
        data_files.append(('share/omf/gnome-app-install',
                           glob.glob("help/*/*.omf")))
        distutils.cmd.Command.run(self)

class build_icons(distutils.cmd.Command):
    def run(self):
        data_files = self.distribution.data_files
        for size in glob.glob("data/icons/*"):
            for category in glob.glob("%s/*" % size):
                icons = []
                for icon in glob.glob("%s/*" % category):
                    icons.append(icon)
                    data_files.append(("share/icons/hicolor/%s/%s" % \
                                       (os.path.basename(size), \
                                        os.path.basename(category)), \
                                        icons))
        distutils.cmd.Command.run(self)

class build_l10n(distutils.cmd.Command):
    def run(self):
        """
        Update the language files, create mo file out of them and add them
        to the to be installed files
        """
        data_files = self.distribution.data_files
        for filepath in glob.glob("po/mo/*/LC_MESSAGES/*.mo"):
            lang = filepath[len("po/mo/"):]
            targetpath = os.path.dirname(os.path.join("share/locale",lang))
            data_files.append((targetpath, [filepath]))

        # HACK: make sure that the mo files are generated and up-to-date
        os.system("intltool-merge -d po data/gnome-app-install.schemas.in"\
                  " build/gnome-app-install.schemas")
        os.system("cd po; make update-po")
        os.system("cd data; make")

        distutils.cmd.Command.run(self)

