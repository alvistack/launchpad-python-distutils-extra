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

        (o, e, s) = self.do_install()
        self.assertEqual(e, '')
        self.assertEqual(s, 0)

        f = self.installed_files()
        # just installs the .egg_info
        self.assertEqual(len(f), 1)
        self.assert_(f[0].endswith('.egg-info'))

    def test_packages(self):
        '''Python packages'''

        self._mksrc('foopkg/__init__.py', '')
        self._mksrc('foopkg/bar.py')
        self._mksrc('foopkg/baz.py')
        self._mksrc('noinit/notme.py')

        (o, e, s) = self.do_install()
        self.assertEqual(e, '')
        self.assertEqual(s, 0)

        f = '\n'.join(self.installed_files())
        self.assert_('foopkg/__init__.py' in f)
        self.assert_('foopkg/bar.py' in f)
        self.failIf('noinit' in f)

    def test_dbus(self):
        '''D-BUS configuration and service files'''

        # D-BUS ACL configuration file
        self._mksrc('daemon/com.example.foo.conf', '''<!DOCTYPE busconfig PUBLIC
 "-//freedesktop//DTD D-BUS Bus Configuration 1.0//EN"
 "http://www.freedesktop.org/standards/dbus/1.0/busconfig.dtd">
<busconfig>
</busconfig>''')

        # non-D-BUS configuration file
        self._mksrc('daemon/defaults.conf', 'start = True\nlog = syslog')

        # D-BUS system service
        self._mksrc('daemon/com.example.foo.service', '''[D-BUS Service]
Name=com.example.Foo
Exec=/usr/lib/foo/foo_daemon
User=root''')

        # D-BUS session service
        self._mksrc('gui/com.example.foo.gui.service', '''[D-BUS Service]
Name=com.example.Foo.GUI
Exec=/usr/bin/foo-gtk
''')

        # non-D-BUS .service file
        self._mksrc('stuff/super.service', 'I am a file')

        (o, e, s) = self.do_install()
        self.assertEqual(e, '')
        self.assertEqual(s, 0)

        f = self.installed_files()
        self.assertEqual(len(f), 4) # 3 D-BUS files plus .egg-info
        self.assert_('/etc/dbus-1/system.d/com.example.foo.conf' in f)
        self.assert_('/usr/local/share/dbus-1/system-services/com.example.foo.service' in f)
        self.assert_('/usr/local/share/dbus-1/services/com.example.foo.gui.service' in f)
        self.failIf('super.service' in '\n'.join(f))

    def test_po(self):
        '''gettext *.po files'''

        self._mkpo()

        (o, e, s) = self.do_install()
        self.assertEqual(e, '')
        self.assertEqual(s, 0)
        f = self.installed_files()
        self.assert_('/usr/local/share/locale/de/LC_MESSAGES/foo.mo' in f)
        self.assert_('/usr/local/share/locale/fr/LC_MESSAGES/foo.mo' in f)
        self.failIf('junk' in '\n'.join(f))

        msgunfmt = subprocess.Popen(['msgunfmt',
            os.path.join(self.install_tree,
            'usr/local/share/locale/de/LC_MESSAGES/foo.mo')],
            stdout=subprocess.PIPE)
        out = msgunfmt.communicate()[0]
        self.assertEqual(out, open(os.path.join(self.src, 'po/de.po')).read())

    def test_policykit(self):
        '''*.policy.in PolicyKit files'''

        self._mksrc('daemon/com.example.foo.policy.in', '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE policyconfig PUBLIC
 "-//freedesktop//DTD PolicyKit Policy Configuration 1.0//EN"
 "http://www.freedesktop.org/standards/PolicyKit/1.0/policyconfig.dtd">
<policyconfig>
  <vendor>Foo project</vendor>
  <vendor_url>https://foo.example.com</vendor_url>

  <action id="com.example.foo.greet">
    <_description>Good morning</_description>
    <_message>Hello</_message>
    <defaults>
      <allow_active>yes</allow_active>
    </defaults>
  </action>
</policyconfig>''')

        self._mkpo()
        (o, e, s) = self.do_install()
        self.assertEqual(e, '')
        self.assertEqual(s, 0)

        f = self.installed_files()
        self.assert_('/usr/local/share/PolicyKit/policy/com.example.foo.policy' in f)
        p = open(os.path.join(self.install_tree,
            'usr/local/share/PolicyKit/policy/com.example.foo.policy')).read()
        self.assert_('<description>Good morning</description>' in p)
        self.assert_('<description xml:lang="de">Guten Morgen</description>' in p)
        self.assert_('<message>Hello</message>' in p)
        self.assert_('<message xml:lang="de">Hallo</message>' in p)

    def test_desktop(self):
        '''*.desktop.in files'''

        self._mksrc('gui/foogtk.desktop.in', '''[Desktop Entry]
_Name=Hello
_Comment=Good morning
Exec=/bin/foo''')
        self._mksrc('gui/autostart/fooapplet.desktop.in', '''[Desktop Entry]
_Name=Hello
_Comment=Good morning
Exec=/usr/bin/fooapplet''')
        self._mkpo()

        (o, e, s) = self.do_install()
        self.assertEqual(e, '')
        self.assertEqual(s, 0)

        f = self.installed_files()
        self.assert_('/usr/local/share/autostart/fooapplet.desktop' in f)
        self.assert_('/usr/local/share/applications/foogtk.desktop' in f)

        p = open(os.path.join(self.install_tree,
            'usr/local/share/autostart/fooapplet.desktop')).read()
        self.assert_('\nName=Hello\n' in p)
        self.assert_('\nName[de]=Hallo\n' in p)
        self.assert_('\nComment[fr]=Bonjour\n' in p)

    def test_icons(self):
        '''data/icons/'''

        self._mksrc('data/icons/scalable/actions/press.png')
        self._mksrc('data/icons/48x48/apps/foo.png')

        (o, e, s) = self.do_install()
        self.assertEqual(e, '')
        self.assertEqual(s, 0)

        f = self.installed_files()
        self.assert_('/usr/local/share/icons/hicolor/scalable/actions/press.png' in f)
        self.assert_('/usr/local/share/icons/hicolor/48x48/apps/foo.png' in f)

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

        return self.setup_py(['install', '--no-compile', '--root=' + self.install_tree])

    def installed_files(self):
        '''Return list of file paths in install tree.'''

        result = []
        for root, _, files in os.walk(self.install_tree):
            assert root.startswith(self.install_tree)
            r = root[len(self.install_tree):]
            for f in files:
                result.append(os.path.join(r, f))
        return result

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

    def _mkpo(self):
        '''Create some example po files.'''

        self._mksrc('po/POTFILES.in', '')
        self._mksrc('po/de.po', '''msgid ""
msgstr "Content-Type: text/plain; charset=UTF-8\\n"

msgid "Good morning"
msgstr "Guten Morgen"

msgid "Hello"
msgstr "Hallo"''')
        self._mksrc('po/fr.po', '''msgid ""
msgstr "Content-Type: text/plain; charset=UTF-8\\n"
        
msgid "Good morning"
msgstr "Bonjour"''')

unittest.main()
