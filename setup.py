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
	author_email = "michal.goral@mgoral.org",
	url = "https://github.com/virgoerns/subconvert",
	license = "GPLv3+",
	scripts = ["subconvert.py"],
)

