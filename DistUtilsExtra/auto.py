'''DistUtilsExtra.auto

This provides a setup() method for distutils and DistUtilsExtra which infers as
many setup() arguments as possible. This includes packages, data files
for GtkBilder, D-Bus, PolicyKit files, scripts, etc.
'''

# (c) 2009 Canonical Ltd.
# Author: Martin Pitt <martin.pitt@ubuntu.com>

import os, os.path, fnmatch
import distutils.core

from DistUtilsExtra.command import *

def setup(**attrs):
    '''Auto-inferring extension of standard distutils.core.setup()

    TODO: doc
    '''
    src = src_find(attrs)

    print '---- attrs before: ----'
    print attrs
    print '---- srcfiles before: ----'
    print src

    __cmdclass(attrs)
    __packages(attrs, src)
    __dbus(attrs, src)

    print '---- attrs after: ----'
    print attrs

    print 'WARNING: the following files are not recognized by DistUtilsExtra.auto:'
    for f in sorted(src):
        print ' ', f

    distutils.core.setup(**attrs)

#
# parts of setup()
#

def __cmdclass(attrs):
    '''Default cmdclass for DistUtilsExtra'''

    v = attrs.setdefault('cmdclass', {})
    v.setdefault('build', build_extra.build_extra)
    v.setdefault('build_i18n', build_i18n.build_i18n)
    v.setdefault('build_icons', build_icons.build_icons)
    v.setdefault('clean', clean_i18n.clean_i18n)

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
        if root.startswith('.') or root.split(os.path.sep, 1)[0] in ('build', 'test', 'tests'):
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
