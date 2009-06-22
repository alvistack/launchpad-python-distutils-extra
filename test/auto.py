#!/usr/bin/python

# test DistUtilsExtra.auto

import sys, unittest, shutil, tempfile, os, os.path, subprocess

class T(unittest.TestCase):
    def setUp(self):
        self.src = tempfile.mkdtemp()

        self._mksrc('setup.py', '''
from DistUtilsExtra.auto import setup

setup(
    name='foo',
    version='0.1',
    description='Test suite package',
    url='https://foo.example.com',
    license='GPL v2 or later',
    author='Martin Pitt',
    author_email='martin.pitt@example.com',
)
''')
        self.snapshot = None
        self.install_tree = None

    def tearDown(self):
        try:
            # check that setup.py clean removes everything
            (o, e, s) = self.setup_py(['clean', '-a'])
            self.assertEqual(e, '')
            self.assertEqual(s, 0)
            cruft = self.diff_snapshot()
            self.assertEqual(cruft, '', 'no cruft after cleaning:\n' + cruft)
        finally:
            shutil.rmtree(self.src)
            if self.snapshot:
                shutil.rmtree(self.snapshot)
            if self.install_tree:
                shutil.rmtree(self.install_tree)
            self.src = None
            self.snapshot = None
            self.install_tree = None

    #
    # actual tests come here
    #

    def test_empty(self):
        '''empty source tree (just setup.py)'''

        self.do_install()
        self.assertEqual(os.listdir(self.install_tree), [])

    #
    # helper methods
    #

    def setup_py(self, args):
        '''Run setup.py with given arguments.

        For convenience, this snapshots the tree if no snapshot exists yet.

        Return (out, err, exitcode) triple.
        '''
        if not self.snapshot:
            self.do_snapshot()

        env = os.environ
        oldcwd = os.getcwd()
        env['PYTHONPATH'] = oldcwd
        os.chdir(self.src)
        s = subprocess.Popen(['python', 'setup.py'] + args, env=env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (out, err) = s.communicate()
        os.chdir(oldcwd)
        return (out, err, s.returncode)

    def do_install(self):
        '''Run setup.py install into temporary tree.

        Return (out, err, exitcode) triple.
        '''
        self.install_tree = tempfile.mkdtemp()

        return self.setup_py(['install', '--root=' + self.install_tree])

    def _mksrc(self, path, content=None, executable=False):
        '''Create a file in the test source tree.'''

        path = os.path.join(self.src, path)
        dir = os.path.dirname(path)
        if not os.path.isdir(dir):
            os.makedirs(dir)
        f = open(path, 'w')
        if content is None:
            # default content, to spot with diff
            print >> f, 'dummy'
        else:
            print >> f, content
        f.close()

        if executable:
            os.chmod(path, 0755)

    def do_snapshot(self):
        '''Snapshot source tree.

        This should be called after a test set up all source files.
        '''
        assert self.snapshot is None, 'snapshot already taken'

        self.snapshot = tempfile.mkdtemp()
        shutil.copytree(self.src, os.path.join(self.snapshot, 's'))

    def diff_snapshot(self):
        '''Compare source tree to snapshot.

        Return diff -Nur output.
        '''
        assert self.snapshot, 'no snapshot taken'
        diff = subprocess.Popen(['diff', '-Nur', os.path.join(self.snapshot, 's'), 
            self.src], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (out, err) = diff.communicate()
        self.assertEqual(err, '', 'diff error messages')
        return out

unittest.main()
