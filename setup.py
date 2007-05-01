#!/usr/bin/env python

from distutils.core import setup
import glob, os, commands, sys


setup(
    name = 'python-distutils-extra',
    version = '0.90',
    author = 'Sebastian Heinlein',
    author_email = 'sebi@glatzor.de',
    description = 'Add support for i18n, documentation and icons to distutils',
    packages = ['DistUtilsExtra', 'DistUtilsExtra.command'],
    license = 'GNU GPL',
    platforms = 'posix',
)
