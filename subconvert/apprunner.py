#-*- coding: utf-8 -*-

"""
Copyright (C) 2011, 2012, 2013 Michal Goral.

This file is part of Subconvert

Subconvert is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Subconvert is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Subconvert. If not, see <http://www.gnu.org/licenses/>.
"""

from PyQt4.QtGui import QApplication

import os
import sys
import signal
import logging
import argparse

from subconvert.utils.Locale import _
from subconvert.utils.version import __appname__, __version__
from subconvert.gui import MainWindow
from subconvert.cli import MainApp
from subconvert.utils.PropertyFile import SubtitleProperties

log = logging.getLogger('Subconvert')

def loadSpf(filePath):
    try:
        spf = SubtitleProperties(filePath)
    except FileNotFoundError:
        log.critical(_("No such file: '%s'") % filePath)
        sys.exit(2)
    return spf

def prepareOptions():
    parser = argparse.ArgumentParser(
        description = _("Subconvert is a movie subtitles editor and converter."))

    parser.add_argument("files", metavar=_("FILE"), nargs="*", type = os.path.expanduser,
        help=_("files to open"))

    parser.add_argument("-c", "--console", action = "store_true",
        help = _("run Subconvert in console"))
    parser.add_argument("-f", "--force", action = "store_true",
        help = _("force all operations without asking (assuming yes)"))


    subtitleGroup = parser.add_argument_group(_("subtitle options"))
    subtitleGroup.add_argument("-o", "--output-file", metavar = _("FILE"), dest = "outputPath",
        type = os.path.expanduser,
        help = _("output file. All occurences of '%%f', will be replaced by input file name base"))
    subtitleGroup.add_argument("-e", "--encoding", metavar = _("ENC"), dest = "inputEncoding",
        type = str,
        help = _("input file encoding"))
    subtitleGroup.add_argument("-E", "--reencode", metavar = _("ENC"), dest = "outputEncoding",
        type = str,
        help = _("change output file encoding to ENC"))
    subtitleGroup.add_argument("-t", "--format", metavar = _("FMT"), dest = "outputFormat",
        type = str,
        help = _("output subtitle format to FMT"))
    subtitleGroup.add_argument("-p", "--property-file", metavar = _("FILE"), dest = "pfile",
        type = loadSpf, default = SubtitleProperties(),
        help = _("load settings from spf (subtitle property file)"))

    movieGroup = parser.add_argument_group(_("movie options"))
    movieGroup.add_argument("--fps", type = float,
        help = _("specify movie frames per second"))
    movieGroup.add_argument("-A", "--auto-fps", action = "store_true", dest = "autoFps",
        help = _("use MPlayer to automatically get FPS value from the movie"))
    movieGroup.add_argument("-v", "--video", metavar = _("MOVIE"), type = os.path.expanduser,
        help = _("specify a video file to get FPS value from. All occurences of '%%f' will be \
            replaced by input file name base"))

    miscGroup = parser.add_argument_group( _("miscellaneous options"))
    miscGroup.add_argument("--debug", action = "store_true",
        help = _("enable debug prints"))
    miscGroup.add_argument("--quiet", action = "store_true",
        help = _("silence Subconvert output"))
    miscGroup.add_argument("--version", action = "store_true",
        help = _("print program version and exit"))

    return parser

def startApp(args):
    if args.console:
        app = MainApp.SubApplication(args)
        sys.exit(app.run())
    else:
        app = QApplication(sys.argv)
        signal.signal(signal.SIGINT, signal.SIG_DFL) # allows ctrl-c which is blocked by default
        gui = MainWindow.MainWindow(args)
        gui.show()
        sys.exit(app.exec_())

def main():
    optParser = prepareOptions()
    args = optParser.parse_args()


    if args.version:
        print("%s %s" % (__appname__, __version__))
        sys.exit(0)

    if args.quiet:
        log.setLevel(logging.ERROR)
    else:
        log.setLevel(logging.INFO)
    if args.debug:
        log.setLevel(logging.DEBUG)
    log.addHandler(logging.StreamHandler())

    startApp(args)
