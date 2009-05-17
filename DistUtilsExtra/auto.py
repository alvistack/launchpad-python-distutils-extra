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
    src = src_find()

    print '---- attrs before: ----'
    print attrs
    print '---- srcfiles before: ----'
    print src

    __cmdclass(attrs)
    __packages(attrs, src)

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
    v.setdefault('build_i18n', build_i18n.build_i18n)
    v.setdefault('build_icons', build_icons.build_icons)

def __packages(attrs, src):
    '''Default packages'''

    if 'packages' in attrs:
        for pkg in attrs['packages']:
            src_mark(src, os.path.join(pkg, '*.py'))
        return

    packages = attrs.setdefault('packages', [])

    for f in src_fileglob(src, '__init__.py'):
        pkg = os.path.dirname(f)
        packages.append(pkg)
        src_mark(src, os.path.join(pkg, '*.py'))


#
# helper functions
#

def src_find():
    '''Find source files.'''

    src = set()
    for (root, dirs, files) in os.walk('.'):
        if root.startswith('./'):
            root = root[2:]
        if root.startswith('build') or root.startswith('.'):
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
            
            src.add(os.path.join(root, f))

    return src

def src_fileglob(src, fnameglob):
    '''Return set of files which match fnameglob.'''

    result = set()
    for f in src:
        if fnmatch.fnmatch(os.path.basename(f), fnameglob):
            result.add(f)
    return result

def src_mark(src, pathglob):
    '''Remove all paths from src which match pathglob.'''

    for f in src.copy():
        if fnmatch.fnmatch(f, pathglob):
            src.remove(f)
