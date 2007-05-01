"""distutils_extra.command.build_l10n

Implements the Distutils 'build_l10n' command."""

import distutils
import glob
import os
import os.path
import re
import sys
import distutils.command.build

class build_l10n(distutils.cmd.Command):

    description = "integrate the gettext framework"

    user_options = [('merge-desktop-files=', None, '.desktop.in files that '
                                                   'should be merged'),
                    ('merge-xml-files=', None, '.xml.in files that should be '
                                               'merged'),
                    ('merge-schemas-files=', None, '.schemas.in files that '
                                                   'should be merged'),
                    ('merge-ba-files=', None, 'bonobo-activation files that '
                                              'should be merged'),
                    ('merge-rfc822deb-files=', None, 'RFC822 files that should '
                                                     'be merged'),
                    ('merge-key-files=', None, '.key.in files that should be '
                                               'merged'),
                    ('domain=', None, 'gettext domain'),
                    ('bug-contact=', None, 'contact address for msgid bugs')]

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
            self.announce("""
WARNING: Intltool will use the values specified from the
         existing po/Makefile in favor of the vaules
         from setup.cfg.
         Remove the Makefile to avoid problems.""")

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

            targetpath = os.path.join("share/locale", lang, "LC_MESSAGES")
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

# class build
