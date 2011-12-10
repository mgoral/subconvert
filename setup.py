#!/usr/bin/env python
#-*- coding: utf-8 -*-

from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages

__AUTHOR__ = "Michał Góral"

setup(
    name = "subconvert",
    description = "Movie subtitles converter",
    author = __AUTHOR__,
    version = "0.8.2",
    author_email = "michal.goral@mgoral.org",
    url = "https://github.com/virgoerns/subconvert",
    license = "GPLv3+",
    package_dir = {'':'src'},
    packages = find_packages(),
    py_modules = ["subparser.Convert", "subparser.FrameTime", \
        "subparser.Parsers", "subparser.SubParser", \
        "subconvert", "subconvert_gui", "subconvert_update"],
    entry_points = {
        'console_scripts' : [
            'subconvert = subconvert:main',
            'subconvert-update = subconvert_update:main',
        ],
        'gui_scripts': [
            'subconvert-gui = subconvert_gui:main',
        ]
    },
)

