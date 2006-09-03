#!/usr/bin/env python

from distutils.core import setup
import glob, os, commands, sys


setup(
    name = 'python-snippets',
    version = '0.0.1',
    description = 'Abstratcion of the sources.list',
    packages = ['Snippets'],
    license = 'GNU GPL',
    platforms = 'posix',
)
