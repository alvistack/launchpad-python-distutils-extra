#!/usr/bin/env python

from distutils.core import setup
import glob, os, commands, sys


setup(
    name = 'python-distutils-extra',
    version = '0.90',
    description = 'Add support for i10n, documentation and icons to distutils',
    packages = ['DistUtilsExtra'],
    license = 'GNU GPL',
    platforms = 'posix',
)
