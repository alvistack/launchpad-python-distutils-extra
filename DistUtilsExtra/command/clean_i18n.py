"""distutils_extra.command.clean_i18n

Implements the Distutils 'clean_i18n' command."""

import os
import os.path

import distutils.command.clean
from distutils.dir_util import remove_tree


class clean_i18n(distutils.command.clean.clean):
    description = "clean up files generated by build_i18n"

    def run(self):
        # clean build/mo
        mo_dir = os.path.join("build", "mo")
        if os.path.isdir(mo_dir):
            remove_tree("build/mo")

        # clean built i18n files
        for setname in (
            "xml_files",
            "desktop_files",
            "schemas_files",
            "rfc822deb_files",
            "ba_files",
            "key_files",
        ):
            file_set = eval(
                self.distribution.get_option_dict("build_i18n").get(
                    setname, (None, "[]")
                )[1]
            )
            for target, files in file_set:
                build_target = os.path.join("build", target)
                for file in files:
                    if file.endswith(".in"):
                        file_merged = os.path.basename(file[:-3])
                    else:
                        file_merged = os.path.basename(file)
                    file_merged = os.path.join(build_target, file_merged)
                    if os.path.exists(file_merged):
                        os.unlink(file_merged)
                if os.path.exists(build_target):
                    os.removedirs(build_target)

        distutils.command.clean.clean.run(self)
