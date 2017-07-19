import os
import sys
import subprocess

import distutils.command.build as distutils_build
from setuptools import setup, find_packages, Command

class NoOptsCmd(Command):
    def initialize_options(self):
        pass
    def finalize_options(self):
        pass

class BuildQrc(NoOptsCmd):
    """Builds qrc files with pyrcc"""
    user_options = []

    def run(self):
        basepath = os.path.dirname(__file__)
        subc_dir = os.path.join(basepath, 'src', 'subconvert')
        in_ = os.path.join(subc_dir, 'resources.qrc')
        out = os.path.join(subc_dir, 'resources.py')
        subprocess.check_call(['pyrcc5', '-o', out, in_])


class SubcBuild(distutils_build.build):
    """Overrides a default install_data"""
    user_options = []

    def run(self):
        self.run_command('build_qrc')
        super().run()


with open('README.md', encoding='utf-8') as f_:
    long_description = f_.read()


def main():
    setup(name='subconvert',
          description='Movie subtitles converter',
          long_description=long_description,
          use_scm_version=True,
          license='GPLv3+',
          author='Michał Góral',
          author_email='dev@mgoral.org',
          url='https://github.com/mgoral/subconvert',
          platforms=['linux'],
          setup_requires=['setuptools_scm'],
          install_requires=['chardet>=3.0',
                            ' PyQt5==5.8.2 '
                           ],

          # https://pypi.python.org/pypi?%3Aaction=list_classifiers
          classifiers=['Development Status :: 6 - Mature',
                       'Environment :: Console',
                       'Environment :: X11 Applications :: Qt',
                       'Intended Audience :: End Users/Desktop',
                       'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
                       'Natural Language :: English',
                       'Operating System :: POSIX',
                       'Programming Language :: Python :: 3 :: Only',
                       'Programming Language :: Python :: 3.2',
                       'Programming Language :: Python :: 3.3',
                       'Programming Language :: Python :: 3.4',
                       'Programming Language :: Python :: 3.5',
                       'Programming Language :: Python :: 3.6',
                       'Topic :: Utilities',
                       ],

          packages=find_packages('src'),
          package_dir={'': 'src'},
          include_package_data=True,
          entry_points={
              'console_scripts': ['subconvert=subconvert.apprunner:main'],
          },
          cmdclass={
              'build': SubcBuild,
              'build_qrc': BuildQrc,
          }
    )

if __name__ == '__main__':
    assert sys.version_info >= (3, 2)
    main()
