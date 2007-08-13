#!/usr/bin/env python

from setuptools import setup
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
    entry_points = {"distutils.commands": [
           "build = DistUtilsExtra.command.build_extra:build",
           "build_i18n = DistUtilsExtra.command.build_i18n:build_i18n",
           "build_icons = DistUtilsExtra.command.build_icons:build_icons",
           "build_help = DistUtilsExtra.command.build_help:build_help",],},
)
