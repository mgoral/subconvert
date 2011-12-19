#!/usr/bin/env python
#-*- coding: utf-8 -*-

from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages


setup(
    name = "subconvert",
    description = "Movie subtitles converter",
    author = "Michał Góral",
    version = "0.8.2",
    author_email = "michal.goral@mgoral.org",
    url = "https://github.com/virgoerns/subconvert",
    download_url = "https://github.com/virgoerns/subconvert/zipball/master",
    license = "GPLv3+",
    install_requires = ['chardet'],
    package_dir = {'':'src'},
    packages = find_packages(exclude=["test"]),
    py_modules = ["subparser.Convert", "subparser.FrameTime", \
        "subparser.Parsers", "subparser.SubParser", "subparser.version", \
        "subconvert", "subconvert_gui"],
    entry_points = {
        'console_scripts' : [
            'subconvert = subconvert:main',
        ],
        'gui_scripts': [
            'subconvert-gui = subconvert_gui:main',
        ]
    },
)

