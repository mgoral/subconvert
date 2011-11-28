#!/usr/bin/env python
#-*- coding: utf-8 -*-

from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup

__AUTHOR__ = "Michał Góral"

setup(
	name = "subconvert",
	description = "Movie subtitles converter",
	author = __AUTHOR__,
	version = 0.8,
	author_email = "michal.goral@mgoral.org",
	url = "https://github.com/virgoerns/subconvert",
	license = "GPLv3+",
	py_modules = ["subconvert", "subconvert_gui"],
	entry_points = {
		'console_scripts' : [
			'subconvert = subconvert:main',
		],
		'gui_scripts': [
			'subconvert-gui = subconvert_gui:main',
		]
	},
)
