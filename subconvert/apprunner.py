#-*- coding: utf-8 -*-

"""
This file is part of SubConvert.

SubConvert is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

SubConvert is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with SubConvert.  If not, see <http://www.gnu.org/licenses/>.
"""

from PyQt4.QtGui import QApplication

import sys
import logging
import argparse

from subconvert.utils.Locale import _
from subconvert.gui import MainWindow

MAX_MEGS = 5 * 1048576

def prepareOptions():
    parser = argparse.ArgumentParser(
        description = _("Subconvert is a movie subtitles editor and converter."))
    parser.add_argument("files", metavar="FILE", nargs="*",
        help=_("files to open."))

    parser.add_argument("--debug", action="store_true",
        help=_("enable debug prints."))
    parser.add_argument("-q", "--quiet", action="store_true",
        help=_("silence Subconvert output."))

    return parser

def startApp():
    app = QApplication(sys.argv)
    gui = MainWindow.MainWindow()
    sys.exit(app.exec_())

def main():
    optParser = prepareOptions()
    args = optParser.parse_args()

    log = logging.getLogger('subconvert')

    if args.quiet:
        log.setLevel(logging.ERROR)
    else:
        log.setLevel(logging.INFO)
    if args.debug:
        log.setLevel(logging.DEBUG)
    log.addHandler(logging.StreamHandler())

    startApp()
