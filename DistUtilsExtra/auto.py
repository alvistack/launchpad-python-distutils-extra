'''DistUtilsExtra.auto

This provides a setup() method for distutils and DistUtilsExtra which infers as
many setup() arguments as possible. This includes packages, data files
for GtkBilder, D-Bus, PolicyKit files, scripts, etc.
'''

# (c) 2009 Canonical Ltd.
# Author: Martin Pitt <martin.pitt@ubuntu.com>

import os, os.path
import distutils.core

from DistUtilsExtra.command import *

def setup(**attrs):
    '''Auto-inferring extension of standard distutils.core.setup()

    TODO: doc
    '''
    src = find_src_files()

    print '---- attrs before: ----'
    print attrs
    print '---- srcfiles before: ----'
    print src

    __cmdclass(attrs)

    print '---- attrs after: ----'
    print attrs

    print 'WARNING: the following files are not recognized by DistUtilsExtra.auto:'
    for f in sorted(src):
        print ' ', f

    print src

    distutils.core.setup(**attrs)

#
# parts of setup()
#

def __cmdclass(attrs):
    '''Default cmdclass for DistUtilsExtra'''

    v = attrs.setdefault('cmdclass', {})
    v.setdefault('build_i18n', build_i18n.build_i18n)
    v.setdefault('build_icons', build_icons.build_icons)

#
# helper functions
#

def find_src_files():
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
