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
        def has_icons(self):
            return self.icons

        def has_l10n(self):
            return self.l10n

        def has_help(self):
            return self.help

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

    description = "install a docbook based documentation"

    user_options= [('help_dir', 'h', 'help directory of the source tree')]

    def initialize_options(self):
        self.help_dir = None

    def finalize_options(self):
        if self.help_dir is None:
            self.help_dir = os.path.join("help")

    def run(self):
        data_files = self.distribution.data_files

        print "Setting up help files..."
        for filepath in glob.glob("help/*"):
            lang = filepath[len("help/"):]
            print " Language: %s" % lang
            path_xml = os.path.join("share/gnome/help",
                                    self.distribution.metadata.name,
                                    lang)
            path_figures = os.path.join("share/gnome/help",
                                        self.distribution.metadata.name,
                                        lang, "figures")
            data_files.append((path_xml, (glob.glob("%s/*.xml" % filepath))))
            data_files.append((path_figures,
                               (glob.glob("%s/figures/*.png" % filepath))))
        data_files.append((os.path.join('share/omf',
                                         self.distribution.metadata.name),
                           glob.glob("help/*/*.omf")))

class build_icons(distutils.cmd.Command):

    description = "select all icons for installation"

    user_options= [('icon_dir', 'i', 'icon directory of the source tree')]

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

class build_l10n(distutils.cmd.Command):

    description = "integrate the gettext framework"

    user_options = [('merge-desktop-files=', 'm', '.desktop.in files that '
                                                  'should be merged'),
                    ('merge-xml-files=', 'x', '.xml.in files that should be '
                                              'merged'),
                    ('merge-schemas-files=', 's', '.schemas.in files that '
                                                  'should be merged'),
                    ('merge-ba-files=', 'b', 'bonobo-activation files that '
                                             'should be merged'),
                    ('merge-rfc822deb-files=', 'd', 'RFC822 files that should '
                                                    'be merged'),
                    ('merge-key-files=', 'k', '.key.in files that should be '
                                              'merged'),
                    ('domain=', 'd', 'gettext domain'),
                    ('bug-contact=', 'c', 'contact address for msgid bugs')]

    def initialize_options(self):
        self.merge_desktop_files = []
        self.merge_xml_files = []
        self.merge_key_files = []
        self.merge_schemas_files = []
        self.merge_ba_files = []
        self.merge_rfc822deb_files = []
        self.domain = None
        self.bug_contact = None

    def finalize_options(self):
        if self.domain is None:
            self.domain = self.distribution.metadata.name

    def run(self):
        """
        Update the language files, generate mo files and add them
        to the to be installed files
        """
        data_files = self.distribution.data_files

        # Print a warning if there is a Makefile that would overwrite our
        # values
        if os.path.exists("po/Makefile"):
            print """
WARNING: Intltool will use the values specified from the
         existing po/Makefile in favor of the vaules
         from setup.cfg.
         Remove the Makefile to avoid problems."""

        # Update the pot file
        command = ""
        if self.bug_contact is not None:
            command = "XGETTEXT_ARGS=--msgid-bugs-address=%s " % self.bug_contact
        command = "cd po; %s intltool-update -p -g %s" % (command, self.domain)
        os.system(command)

        # Merge new strings into the po files
        command = ""
        if self.bug_contact is not None:
            command = "XGETTEXT_ARGS=--msgid-bugs-address=%s " % self.bug_contact
        command = "cd po; %s intltool-update -r -g %s" % (command, self.domain)
        os.system(command)

        for po_file in glob.glob("po/*.po"):
            lang = os.path.basename(po_file[:-3])
            mo_dir =  os.path.join("build", "mo", lang, "LC_MESSAGES")
            mo_file = os.path.join(mo_dir, "%s.mo" % self.domain)
            if not os.path.exists(mo_dir):
                os.makedirs(mo_dir)
            os.system("msgfmt %s -o %s" % (po_file, mo_file))

            targetpath = os.path.dirname(os.path.join("share/locale",lang,
                                                      "LC_MESSAGES"))
            data_files.append((targetpath, (mo_file,)))

        # merge .in with translation
        for (intltool_type, option) in ((self.merge_xml_files, "-x"),
                                        (self.merge_desktop_files, "-d"),
                                        (self.merge_schemas_files, "-s"),
                                        (self.merge_rfc822deb_files, "-r"),
                                        (self.merge_ba_files, "-b"),
                                        (self.merge_key_files, "-k"),):
            try:
                intltool_type = eval(intltool_type)
            except:
                continue
            for (target, files) in intltool_type:
                build_target = os.path.join("build", target)
                files_merged = []
                for file in files:
                    if file.endswith(".in"):
                        file_merged = os.path.basename(file[:-3])
                    else:
                        file_merged = os.path.basename(file)
                if not os.path.exists(build_target): 
                    os.makedirs(build_target)
                file_merged = os.path.join(build_target, file_merged)
                os.system("intltool-merge %s po %s %s" % (option, file, 
                                                          file_merged))
                files_merged.append(file_merged)
                data_files.append((target, files_merged))

