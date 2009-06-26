'''DistUtilsExtra.auto

This provides a setup() method for distutils and DistUtilsExtra which infers as
many setup() arguments as possible. The idea is that your setup.py only needs
to have the metadata and some tweaks for unusual files/paths, in a "convention
over configuration" paradigm.

This currently supports:

 * Python modules (./*.py, only in root directory)
 * Python packages (all directories with __init__.py)
 * GtkBuilder (*.ui)
 * Qt4 user interfaces (*.ui)
 * D-Bus (*.conf and *.service)
 * PolicyKit (*.policy.in)
 * Desktop files (*.desktop.in)
 * KDE4 notifications (*.notifyrc.in)
 * scripts (all in bin/, and ./<projectname>
 * Auxiliary data files (in data/*)
 * automatic po/POTFILES.in (with all source files which contain _())
 * automatic MANIFEST (everything except swap and backup files, *.pyc, and
   revision control)
 * manpages (*.[0-9])

If you follow above conventions, then you don't need any po/POTFILES.in,
./setup.cfg, or ./MANIFEST.in, and just need the project metadata (name,
author, license, etc.) in ./setup.py.
'''

__version__ = '2.2'

# (c) 2009 Canonical Ltd.
# Author: Martin Pitt <martin.pitt@ubuntu.com>

import os, os.path, fnmatch, stat
import distutils.core

from DistUtilsExtra.command import *
from distutils.dir_util import remove_tree
import distutils.command.clean
import distutils.command.sdist
import distutils.filelist

# FIXME: global variable, to share with build_i18n_auto
src = {}
src_all = {}

def setup(**attrs):
    '''Auto-inferring extension of standard distutils.core.setup()'''
    global src
    global src_all
    src_all = src_find(attrs)
    src = src_all.copy()

    src_mark(src, 'setup.py')

    __cmdclass(attrs)
    __modules(attrs, src)
    __packages(attrs, src)
    __dbus(attrs, src)
    __data(attrs, src)
    __scripts(attrs, src)
    __stdfiles(attrs, src)
    __gtkbuilder(attrs, src)
    __manpages(attrs, src)

    distutils.core.setup(**attrs)

    if src:
        print 'WARNING: the following files are not recognized by DistUtilsExtra.auto:'
        for f in sorted(src):
            print ' ', f

#
# parts of setup()
#

class clean_build_tree(distutils.command.clean.clean):

    description = 'clean up build/ directory'

    def run(self):
        # clean build/mo
        if os.path.isdir('build'):
            remove_tree('build')
        distutils.command.clean.clean.run(self)

def __cmdclass(attrs):
    '''Default cmdclass for DistUtilsExtra'''

    v = attrs.setdefault('cmdclass', {})
    v.setdefault('build', build_extra.build_extra)
    v.setdefault('build_i18n', build_i18n_auto)
    v.setdefault('build_icons', build_icons.build_icons)
    v.setdefault('build_kdeui', build_kdeui_auto)
    v.setdefault('clean', clean_build_tree)
    v.setdefault('sdist', sdist_auto)

def __modules(attrs, src):
    '''Default modules'''

    if 'py_modules' in attrs:
        for mod in attrs['py_modules']:
            src_markglob(src, os.path.join(mod, '*.py'))
        return

    mods = attrs.setdefault('py_modules', [])

    for f in src_fileglob(src, '*.py'):
        if os.path.sep not in f:
            mods.append(os.path.splitext(f)[0])
            src_markglob(src, f)

def __packages(attrs, src):
    '''Default packages'''

    if 'packages' in attrs:
        for pkg in attrs['packages']:
            src_markglob(src, os.path.join(pkg, '*.py'))
        return

    packages = attrs.setdefault('packages', [])

    for f in src_fileglob(src, '__init__.py'):
        pkg = os.path.dirname(f)
        packages.append(pkg)
        src_markglob(src, os.path.join(pkg, '*.py'))

def __dbus(attrs, src):
    '''D-Bus configuration and services'''

    v = attrs.setdefault('data_files', [])

    # /etc/dbus-1/system.d/*.conf
    dbus_conf = []
    for f in src_fileglob(src, '*.conf'):
        if '-//freedesktop//DTD D-BUS Bus Configuration' in open(f).read():
            src_mark(src, f)
            dbus_conf.append(f)
    if dbus_conf:
        v.append(('/etc/dbus-1/system.d/', dbus_conf))

    session_service = []
    system_service = []
    # dbus services
    for f in src_fileglob(src, '*.service'):
        lines = [l.strip() for l in open(f).readlines()]
        if '[D-BUS Service]' not in lines:
            continue
        for l in lines:
            if l.startswith('User='):
                src_mark(src, f)
                system_service.append(f)
                break
        else:
            src_mark(src, f)
            session_service.append(f)
    if system_service:
        v.append(('share/dbus-1/system-services', system_service))
    if session_service:
        v.append(('share/dbus-1/services', session_service))

def __data(attrs, src):
    '''Install auxiliary data files.

    This installs everything from data/ except data/icons/ into
    prefix/share/<projectname>/.
    '''
    v = attrs.setdefault('data_files', [])

    assert 'name' in attrs, 'You need to set the "name" property in setup.py'

    data_files = []
    for f in src.copy():
        if f.startswith('data/') and not f.startswith('data/icons/'):
            v.append((os.path.join('share', attrs['name'], os.path.dirname(f[5:])), [f]))
            src_mark(src, f)

def __scripts(attrs, src):
    '''Install scripts.

    This picks executable scripts in bin/*, and an executable ./<projectname>.
    Other scripts have to be added manually; this is to avoid automatically
    installing test suites, build scripts, etc.
    '''
    assert 'name' in attrs, 'You need to set the "name" property in setup.py'

    scripts = []
    for f in src.copy():
        if f.startswith('bin/') or f == attrs['name']:
            st = os.stat(f)
            if stat.S_ISREG(st.st_mode) and st.st_mode & stat.S_IEXEC:
                scripts.append(f)
                src_mark(src, f)

    if scripts:
        v = attrs.setdefault('scripts', [])
        v += scripts

def __stdfiles(attrs, src):
    '''Install/mark standard files.

    This covers COPYING, AUTHORS, README, etc.
    '''
    src_markglob(src, 'COPYING*')
    src_markglob(src, 'LICENSE*')
    src_markglob(src, 'AUTHORS')
    src_markglob(src, 'MANIFEST.in')
    src_markglob(src, 'MANIFEST')
    src_markglob(src, 'TODO')

    # install all README* from the root directory
    readme = []
    for f in src_fileglob(src, 'README*').union(src_fileglob(src, 'NEWS')):
        if os.path.sep not in f:
            readme.append(f)
            src_mark(src, f)
    if readme:
        assert 'name' in attrs, 'You need to set the "name" property in setup.py'

        attrs.setdefault('data_files', []).append((os.path.join('share', 'doc',
            attrs['name']), readme))

def __gtkbuilder(attrs, src):
    '''Install GtkBuilder *.ui files'''

    ui = []
    for f in src_fileglob(src_all, '*.ui'):
        contents = open(f).read()
        if '<interface>\n' in contents and '<requires lib="gtk+"' in contents:
            src_mark(src, f)
            ui.append(f)
    if ui:
        assert 'name' in attrs, 'You need to set the "name" property in setup.py'

        attrs.setdefault('data_files', []).append((os.path.join('share', 
            attrs['name']), ui))

def __manpages(attrs, src):
    '''Install manpages'''

    mans = {}
    for f in src_fileglob(src_all, '*.[0123456789]'):
        line = open(f).readline()
        if line.startswith('.TH '):
            src_mark(src, f)
            mans.setdefault(f[-1], []).append(f)
    v = attrs.setdefault('data_files', [])
    for section, files in mans.iteritems():
        v.append((os.path.join('share', 'man', 'man' + section), files))

#
# helper functions
#

def src_find(attrs):
    '''Find source files.
    
    This ignores all source files which are explicitly specified as setup()
    arguments.
    '''
    src = set()

    # files explicitly covered in setup() call
    explicit = set(attrs.get('scripts', []))
    for (destdir, files) in attrs.get('data_files', []):
        explicit.update(files)

    for (root, dirs, files) in os.walk('.'):
        if root.startswith('./'):
            root = root[2:]
        if root == '.':
            root = ''
        if root.startswith('.') or \
                root.split(os.path.sep, 1)[0] in ('build', 'test', 'tests'):
            continue
        # data/icons is handled by build_icons
        if root.startswith(os.path.join('data', 'icons')):
            continue
        for f in files:
            ext = os.path.splitext(f)[1]
            if f.startswith('.') or ext in ('.pyc', '~', '.mo'):
                continue
            # po/*.po is taken care of by build_i18n
            if root == 'po' and (ext == '.po' or f == 'POTFILES.in'):
                continue
            
            path = os.path.join(root, f)
            if path not in explicit:
                src.add(path)

    return src

def src_fileglob(src, fnameglob):
    '''Return set of files which match fnameglob.'''

    result = set()
    for f in src:
        if fnmatch.fnmatch(os.path.basename(f), fnameglob):
            result.add(f)
    return result

def src_mark(src, path):
    '''Remove path from src.'''

    src.remove(path)

def src_markglob(src, pathglob):
    '''Remove all paths from src which match pathglob.'''

    for f in src.copy():
        if fnmatch.fnmatch(f, pathglob):
            src.remove(f)

#
# Automatic setup.cfg
#

class build_i18n_auto(build_i18n.build_i18n):
    def finalize_options(self):
        build_i18n.build_i18n.finalize_options(self)
        global src

        # add PolicyKit files
        policy_files = []
        for f in src_fileglob(src, '*.policy.in'):
            src_mark(src, f)
            policy_files.append(f)
        if policy_files:
            try:
                xf = eval(self.xml_files)
            except TypeError:
                xf = []
            xf.append(('share/PolicyKit/policy', policy_files))
            self.xml_files = repr(xf)

        # add desktop files
        desktop_files = []
        autostart_files = []
        notify_files = []
        for f in src_fileglob(src, '*.desktop.in'):
            src_mark(src, f)
            if 'autostart' in f:
                autostart_files.append(f)
            else:
                desktop_files.append(f)
        for f in src_fileglob(src, '*.notifyrc.in'):
            src_mark(src, f)
            notify_files.append(f)
        try:
            df = eval(self.desktop_files)
        except TypeError:
            df = []
        if desktop_files:
            df.append(('share/applications', desktop_files))
        if autostart_files:
            df.append(('share/autostart', autostart_files))
        if notify_files:
            df.append(('share/kde4/apps/' + self.distribution.get_name(), notify_files))
        self.desktop_files = repr(df)

        # mark PO template as known to handle
        try:
            src_mark(src, os.path.join('po', self.distribution.get_name() + '.pot'))
        except KeyError:
            pass

    def run(self):
        '''Build a default POTFILES.in'''

        auto_potfiles_in = False
        global src_all
        if not os.path.exists(os.path.join('po', 'POTFILES.in')):
            files = src_fileglob(src_all, '*.py')
            files.update(src_fileglob(src_all, '*.desktop.in'))
            files.update(src_fileglob(src_all, '*.notifyrc.in'))
            files.update(src_fileglob(src_all, '*.policy.in'))

            for f in src_fileglob(src_all, '*.ui'):
                contents = open(f).read()
                if '<interface>\n' in contents and '<requires lib="gtk+"' in contents:
                    files.add('[type: gettext/glade]' + f)

            if files:
                if not os.path.isdir('po'):
                    os.mkdir('po')
                potfiles_in = open('po/POTFILES.in', 'w')
                print >> potfiles_in, '[encoding: UTF-8]'
                for f in files:
                    print >> potfiles_in, f
                potfiles_in.close()

                auto_potfiles_in = True

        build_i18n.build_i18n.run(self)

        if auto_potfiles_in:
            os.unlink('po/POTFILES.in')
            try:
                os.rmdir('po')
            except:
                pass

class build_kdeui_auto(build_kdeui.build_kdeui):
    def finalize_options(self):
        global src

        # add *.ui files which belong to KDE4
        kdeui_files = []
        for f in src_fileglob(src, '*.ui'):
            if open(f).readline().startswith('<ui version="'):
                src_mark(src, f)
                kdeui_files.append(f)
        if kdeui_files:
            try:
                uf = eval(self.ui_files)
            except TypeError:
                uf = []
            uf += kdeui_files
            self.ui_files = repr(uf)

        build_kdeui.build_kdeui.finalize_options(self)

#
# Automatic sdist
#

class sdist_auto(distutils.command.sdist.sdist):
    def add_defaults(self):
        filter_prefix = ['build', '.git', '.svn', '.CVS', '.bzr', 
                os.path.join('dist', self.distribution.get_name())]
        filter_suffix = ['.pyc', '.mo', '~', '.swp']

        distutils.command.sdist.sdist.add_defaults(self)

        manifest_in = os.path.join('MANIFEST.in')
        if os.path.exists(manifest_in):
            return

        for f in distutils.filelist.findall():
            if f in self.filelist.files or any(map(f.startswith, filter_prefix)) or \
                    any(map(f.endswith, filter_suffix)):
                continue
            self.filelist.append(f)

