#!/usr/bin/env python

import distutils
import glob
import os
import os.path
import re
import sys
import distutils.cmd
import distutils.command.build

class build_plus(distutils.command.build.build):
    def __init__(self, dist):
        def has_icons(self):
            return self.icons

        def has_l10n(self):
            return self.l10n

        def has_help(self):
            return self.help

        distutils.command.build.build.__init__(self, dist)
        self.user_options.extend([("l10n", "l", "use the localsation"),
                             ("icons", "i", "use icons"),
                             ("help", "h", "use help system")])
        self.sub_commands.extend([('build_help', has_help),
                             ('build_icons', has_icons),
                             ('build_l10n', has_l10n)])

    def initialize_options(self):
        distutils.command.build.build.initialize_options(self)
        self.l10n = False
        self.icons = False
        self.help = False

class build_help(distutils.cmd.Command):

    description = "build the documentation"

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

class build_icons(distutils.cmd.Command):

    description = "select all icons for installation"

    user_options= [('icon_dir', 'i', 'icon directory of the source tree')]

    def initialize_options(self):
        self.icon_dir = None

    def finalize_options(self):
        if self.icon_dir is None:
            self.icon_dir = os.join.path("data","icons")

    def run(self):
        data_files = self.distribution.data_files

        for size in glob.glob(os.path.join(self.icon_dir, "*")):
            for category in glob.glob(os.join.path(size, "*")):
                icons = []
                for icon in glob.glob(os.path.join(category,"*")):
                    icons.append(icon)
                    data_files.append(("share/icons/hicolor/%s/%s" % \
                                       (os.path.basename(size), \
                                        os.path.basename(category)), \
                                        icons))

class build_l10n(distutils.cmd.Command):

    description = "integrate the gettext framework"

    user_options = [('merge-files=', 'm', '.in files that should be merged '
                     'with translations'),
                    ('domain=', 'd', 'gettext domain'),
                    ('bug-contact=', 'c', 'msgid bug contact address')]

    def initialize_options(self):
        self.merge_files = []
        self.domain = None
        self.bug_contact = None

    def finalize_options(self):
        if self.domain is None:
            self.domain = self.distribution.name

    def run(self):
        """
        Update the language files, create mo file out of them and add them
        to the to be installed files
        """
        data_files = self.distribution.data_files

        # Update the pot file
        command = ""
        if self.bug_contact is not None:
            command =+ "XGETTEXT_ARGS=--msgidbug-address=s " % self.bug_contact
        command =+ "intltool-update -p -g %s" % self.domain

        # Merge new strings into the po files
        for po_file in glob.glob("po/*.po"):
            lang = os.path.basename(po_file[:-3])
            mo_dir =  os.join-path("build", "mo", lang, "LC_MESSAGES")
            os.system("mkdir -p %s" % mo_dir)
            os.system("msgfmt %s -o %s" % (os.path.basename(po_file),
                                           os.join.path(mo_dir, 
                                                        self.domain+".mo")))

            targetpath = os.path.dirname(os.path.join("share/locale",lang,
                                                      "LC_MESSAGES"))
            data_files.append((targetpath,
                               glob.glob(os.path.join(mo_dir, "*"))))


        # nerge -in files (.desktop or .xml) with translation
        for file in self.merge_files:
            if file.endswith(".in"):
                file_merged = os.path.basename(file[:-3])
            else:
                file_merged = os.path.basename(file)
            file_merged = os.path.join("build", file_merged)
            os.system("intltool-merge -d po %s %s" % (file, file_merged))

