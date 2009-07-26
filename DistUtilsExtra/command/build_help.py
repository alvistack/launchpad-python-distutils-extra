"""distutils_extra.command.build_help

Implements the Distutils "build_help" command."""

from distutils.cmd import Command
from glob import glob
from os.path import join, basename

class build_help(Command):
    description = "install a docbook-based documentation"
    user_options= [("help_dir", None, "help directory in the source tree")]
	
    def initialize_options(self):
        self.help_dir = None

    def finalize_options(self):
        if self.help_dir is None:
            self.help_dir = "help"

    def get_data_files(self):
        data_files = []
        name = self.distribution.metadata.name
        omf_pattern = join(self.help_dir, "*/*.omf")

        for path in glob(join(self.help_dir, "*")):
            lang = basename(path)
            path_xml = join("share/gnome/help", lang)
            path_figures = join("share/gnome/help", name, lang, "figures")
            
            data_files.append((path_xml, glob("%s/*.xml" % path)))
            data_files.append((path_figures, glob("%s/figures/*.png" % path)))
        
        data_files.append((join("share/omf", name), glob(omf_pattern)))
        
        return data_files
    
    def run(self):
        self.announce("Setting up help files...")
        
        data_files = self.distribution.data_files
        data_files.extend(self.get_data_files())
