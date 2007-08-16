import unittest
import os
import shutil
from bzrlib.branch import Branch
from bzrlib.plugins.builddeb import cmd_builddeb

class TestBuildGnomeAppInstall(unittest.TestCase):
    def setUp(self):
        #self.branch_url = "http://bazaar.launchpad.net/~ubuntu-core-dev/gnome-app-install/main/"
        self.branch_url = "/home/renate/Entwicklung/gnome-app-install/sebi"
        self.name = "gnome-app-install"

    def testBuild(self):
        """
        Creates a lightweight checkout of the bzr repository and builds
        the package
        """
        branch_path = os.path.join("temp", "%s-bzr" % self.name)
        build_path = os.path.join("temp", "%s-build" % self.name)
        if not os.path.exists("temp"):
            os.mkdir("temp")
        if os.path.exists(branch_path):
            shutil.rmtree(branch_path)
        if os.path.exists(build_path):
            shutil.rmtree(build_path)
        br = Branch.open(self.branch_url)
        wt = br.create_checkout(branch_path, lightweight=True)
        builder = cmd_builddeb()
        builder.run(branch=branch_path, build_dir=build_path,
                    native=True)

class TestBuildUpdateManager(TestBuildGnomeAppInstall):
    def setUp(self):
        #self.branch_url = " https://launchpad.net/~ubuntu-core-dev/+branch/update-manager/main"
        self.branch_url = "/home/renate/Entwicklung/update-manager/main"
        self.name = "update-manager"

class TestDisplayConfigGTK(TestBuildGnomeAppInstall):
    def setUp(self):
        #self.branch_url = " https://launchpad.net/~displayconfig-gtk/displayconfig-gtk/ubuntu/"
        self.branch_url = "/home/renate/Entwicklung/displayconfig/ubuntu"
        self.name = "displayconfig-gtk"

class TestSoftwareProperties(TestBuildGnomeAppInstall):
    def setUp(self):
        #self.branch_url = " http://bazaar.launchpad.net/~ubuntu-core-dev/software-properties/main/"
        self.branch_url = "/home/renate/Entwicklung/software-properties/ubuntu"
        self.name = "software-properties"

if __name__ == '__main__':
        unittest.main()
