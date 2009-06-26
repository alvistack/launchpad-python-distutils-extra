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
        self.failIf('following files are not recognized' in o)

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
        self.assert_('following files are not recognized' in o)
        self.assert_('\n  noinit/notme.py\n' in o)

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
        self.assert_('following files are not recognized' in o)
        self.assert_('\n  stuff/super.service\n' in o)

        f = self.installed_files()
        self.assertEqual(len(f), 4) # 3 D-BUS files plus .egg-info
        self.assert_('/etc/dbus-1/system.d/com.example.foo.conf' in f)
        self.assert_('/usr/share/dbus-1/system-services/com.example.foo.service' in f)
        self.assert_('/usr/share/dbus-1/services/com.example.foo.gui.service' in f)
        self.failIf('super.service' in '\n'.join(f))

    def test_po(self):
        '''gettext *.po files'''

        self._mkpo()

        (o, e, s) = self.do_install()
        self.assertEqual(e, '')
        self.assertEqual(s, 0)
        self.failIf('following files are not recognized' in o)
        f = self.installed_files()
        self.assert_('/usr/share/locale/de/LC_MESSAGES/foo.mo' in f)
        self.assert_('/usr/share/locale/fr/LC_MESSAGES/foo.mo' in f)
        self.failIf('junk' in '\n'.join(f))

        msgunfmt = subprocess.Popen(['msgunfmt',
            os.path.join(self.install_tree,
            'usr/share/locale/de/LC_MESSAGES/foo.mo')],
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
        self.failIf('following files are not recognized' in o)

        f = self.installed_files()
        self.assert_('/usr/share/PolicyKit/policy/com.example.foo.policy' in f)
        p = open(os.path.join(self.install_tree,
            'usr/share/PolicyKit/policy/com.example.foo.policy')).read()
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
        self.failIf('following files are not recognized' in o)

        f = self.installed_files()
        self.assert_('/usr/share/autostart/fooapplet.desktop' in f)
        self.assert_('/usr/share/applications/foogtk.desktop' in f)

        p = open(os.path.join(self.install_tree,
            'usr/share/autostart/fooapplet.desktop')).read()
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
        self.failIf('following files are not recognized' in o)

        f = self.installed_files()
        self.assert_('/usr/share/icons/hicolor/scalable/actions/press.png' in f)
        self.assert_('/usr/share/icons/hicolor/48x48/apps/foo.png' in f)

    def test_data(self):
        '''Auxiliary files in data/'''

        # have some explicitly covered files, to check that they don't get
        # installed into prefix/share/foo/ again
        self._mksrc('setup.py', '''
from DistUtilsExtra.auto import setup
from glob import glob

setup(
    name='foo',
    version='0.1',
    description='Test suite package',
    url='https://foo.example.com',
    license='GPL v2 or later',
    author='Martin Pitt',
    author_email='martin.pitt@example.com',

    data_files = [
      ('/lib/udev/rules.d', ['data/40-foo.rules']),
      ('/etc/foo', glob('data/*.conf')),
    ]
)
''')

        self._mksrc('data/stuff')
        self._mksrc('data/handlers/red.py', 'import sys\nprint "RED"')
        self._mksrc('data/handlers/blue.py', 'import sys\nprint "BLUE"')
        self._mksrc('data/40-foo.rules')
        self._mksrc('data/blob1.conf')
        self._mksrc('data/blob2.conf')

        (o, e, s) = self.do_install()
        self.assertEqual(e, '')
        self.assertEqual(s, 0)
        self.failIf('following files are not recognized' in o)

        f = self.installed_files()
        self.assert_('/usr/share/foo/stuff' in f)
        self.assert_('/usr/share/foo/handlers/red.py' in f)
        self.assert_('/usr/share/foo/handlers/blue.py' in f)
        self.assert_('/lib/udev/rules.d/40-foo.rules' in f)
        self.assert_('/etc/foo/blob1.conf' in f)
        self.assert_('/etc/foo/blob2.conf' in f)
        self.failIf('/usr/share/foo/blob1.conf' in f)
        self.failIf('/usr/share/foo/40-foo.rules' in f)

    def test_scripts(self):
        '''scripts'''

        # these should get autoinstalled
        self._mksrc('bin/yell', '#!/bin/sh', True)
        self._mksrc('bin/shout', '#!/bin/sh', True)
        self._mksrc('bin/foo', '#!/bin/sh', True)

        # these shouldn't
        self._mksrc('daemon/food', '#!/bin/sh', True) # not in bin/
        self._mksrc('foob', '#!/bin/sh', True) # not named like project
        self._mksrc('bin/whisper', '#!/bin/sh') # not executable

        (o, e, s) = self.do_install()
        self.assertEqual(e, '')
        self.assertEqual(s, 0)
        self.assert_('following files are not recognized' in o)
        self.assert_('\n  foob' in o)
        self.assert_('\n  bin/whisper' in o)
        self.assert_('\n  daemon/food' in o)

        f = self.installed_files()
        self.assert_('/usr/bin/yell' in f)
        self.assert_('/usr/bin/shout' in f)
        self.assert_('/usr/bin/foo' in f)
        ftext = '\n'.join(f)
        self.failIf('food' in ftext)
        self.failIf('foob' in ftext)
        self.failIf('whisper' in ftext)

        # verify that they are executable
        binpath = os.path.join(self.install_tree, 'usr', 'bin')
        self.assert_(os.access(os.path.join(binpath, 'yell'), os.X_OK))
        self.assert_(os.access(os.path.join(binpath, 'shout'), os.X_OK))
        self.assert_(os.access(os.path.join(binpath, 'foo'), os.X_OK))

    def test_pot_manual(self):
        '''PO template creation with manual POTFILES.in'''

        self._mk_i18n_source()
        self._mksrc('po/foo.pot', '')
        # only do a subset here
        self._mksrc('po/POTFILES.in', '''
gtk/main.py
gui/foo.desktop.in
[type: gettext/glade]gtk/test.ui''')

        (o, e, s) = self.setup_py(['build'])
        self.assertEqual(e, '')
        self.assertEqual(s, 0)
        # POT file should not be shown as not recognized
        self.failIf('\n  po/foo.pot\n' in o)

        pot_path = os.path.join(self.src, 'po', 'foo.pot')
        self.assert_(os.path.exists(pot_path))
        pot = open(pot_path).read()

        self.failIf('msgid "no"' in pot)
        self.assert_('msgid "yes1"' in pot)
        self.assert_('msgid "yes2 %s"' in pot)
        self.failIf('msgid "yes5"' in pot) # we didn't add helpers.py
        self.assert_('msgid "yes7"' in pot) # we did include the desktop file
        self.failIf('msgid "yes5"' in pot) # we didn't add helpers.py
        self.assert_('msgid "yes11"' in pot) # we added the GTKBuilder file

    def test_pot_auto(self):
        '''PO template creation with automatic POTFILES.in'''

        self._mk_i18n_source()

        (o, e, s) = self.setup_py(['build'])
        self.assertEqual(e, '')
        self.assertEqual(s, 0)
        # POT file should not be shown as not recognized
        self.failIf('\n  po/foo.pot\n' in o)

        pot_path = os.path.join(self.src, 'po', 'foo.pot')
        self.assert_(os.path.exists(pot_path))
        pot = open(pot_path).read()

        self.failIf('msgid "no"' in pot)
        for i in range(2, 12):
            self.assert_('msgid "yes%i' % i in pot or 
                   'msgid ""\n"yes%i' % i in pot,
                   'yes%i' % i)
        # above loop would match yes11 to yes1 as well, so test it explicitly
        self.assert_('msgid "yes1"' in pot)

    def test_standard_files(self):
        '''Standard files (MANIFEST.in, COPYING, etc.)'''

        self._mksrc('AUTHORS')
        self._mksrc('COPYING')
        self._mksrc('LICENSE')
        self._mksrc('COPYING.LIB')
        self._mksrc('README.txt')
        self._mksrc('MANIFEST.in')
        self._mksrc('MANIFEST')

        (o, e, s) = self.do_install()
        self.assertEqual(e, '')
        self.assertEqual(s, 0)
        self.failIf('following files are not recognized' in o, o)

        f = self.installed_files()
        self.assert_('/usr/share/doc/foo/README.txt' in f)
        ftext = '\n'.join(f)
        self.failIf('MANIFEST' in ftext)
        self.failIf('COPYING' in ftext)
        self.failIf('COPYING' in ftext)
        self.failIf('AUTHORS' in ftext)

        # sub-dir READMEs shouldn't be installed by default
        self.snapshot = None
        self._mksrc('extra/README')
        (o, e, s) = self.do_install()
        self.assertEqual(e, '')
        self.assertEqual(s, 0)
        self.assert_('following files are not recognized' in o)
        self.assert_('\n  extra/README\n' in o)

    def test_sdist(self):
        '''default MANIFEST'''

        good = ['AUTHORS', 'README.txt', 'COPYING', 'helpers.py',
                'foo/__init__.py', 'foo/bar.py', 'tests/all.py',
                'gui/x.desktop.in', 'backend/foo.policy.in',
                'daemon/backend.conf', 'x/y', 'po/de.po', 'po/foo.pot',
                '.quickly', 'data/icons/16x16/apps/foo.png', 'bin/foo',
                'backend/food', 'backend/com.example.foo.service',
                'gtk/main.glade', 'dist/extra.tar.gz']
        bad = ['po/de.mo', '.helpers.py.swp', '.bzr/index', '.svn/index',
               '.git/index', 'bin/foo~', 'backend/foo.pyc', 
               'dist/foo-0.1.tar.gz']

        for f in good + bad:
            self._mksrc(f)

        (o, e, s) = self.setup_py(['sdist', '-o'])
        self.assert_("'MANIFEST.in' does not exist" in e)
        self.assertEqual(s, 0)

        manifest = open(os.path.join(self.src, 'MANIFEST')).read().splitlines()

        for f in good:
            self.assert_(f in manifest, '%s in manifest' % f)
        for f in bad:
            self.failIf(f in manifest, '%s not in manifest' % f)
        os.unlink(os.path.join(self.src, 'MANIFEST'))

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

        return self.setup_py(['install', '--no-compile', '--prefix=/usr', 
            '--root=' + self.install_tree])

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
        diff = subprocess.Popen(['diff', '-x', 'foo.pot', '-Nur', os.path.join(self.snapshot, 's'), 
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

    def _mk_i18n_source(self):
        '''Create some example source files with gettext calls'''

        self._mksrc('gtk/main.py', '''print _("yes1")
print "no1"
print __("no2")
x = _('yes2 %s') % y

def f():
    print _(u"yes3")
    return _(u'yes6')''')

        self._mksrc('helpers.py', '''
print f(_(u"yes4"))
print _(\'\'\'yes5
even more
lines\'\'\')
print _("""yes6
more lines""")
print \'\'\'no3
boo\'\'\'
print """no4
more"""''')

        self._mksrc('gui/foo.desktop.in', '''[Desktop Entry]
_Name=yes7
_Comment=yes8
Icon=no5
Exec=/usr/bin/foo''')

        self._mksrc('daemon/com.example.foo.policy.in', '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE policyconfig PUBLIC
 "-//freedesktop//DTD PolicyKit Policy Configuration 1.0//EN"
 "http://www.freedesktop.org/standards/PolicyKit/1.0/policyconfig.dtd">
<policyconfig>
  <action id="com.example.foo.greet">
    <_description>yes9</_description>
    <_message>yes10</_message>
    <defaults>
      <allow_active>no6</allow_active>
    </defaults>
  </action>
</policyconfig>''')

        self._mksrc('gtk/test.ui', '''<?xml version="1.0"?>
<interface>
  <requires lib="gtk+" version="2.16"/>
  <object class="GtkWindow" id="window1">
    <property name="title" translatable="yes">yes11</property>
    <child><placeholder/></child>
  </object>
</interface>''')

        self._mksrc('Makefile', 'echo _("no7")')

unittest.main()