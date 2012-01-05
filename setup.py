#!/usr/bin/env python
#-*- coding: utf-8 -*-

try:
    from ez_setup import use_setuptools
    use_setuptools()
except:
    print "I will not be able to automatically install setuptools. You have to install it manually if it's not present in your system (usually try 'aptitude install python-setuptools')."

from setuptools import setup, find_packages


setup(
    name = "subconvert",
    description = "Movie subtitles converter",
    long_description = "SubConvert is a movie subtitle converter that supports\
    many different formats, guessing file(s) encoding and fetching movie FPS.\
    For more details refer to README file.",
    author = "Michał Góral",
    maintainer = "Michał Góral",
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

    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: X11 Applications :: Qt',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.6',
        'Topic :: Utilities',
    ],
)

