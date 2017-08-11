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

import os
import sys
import logging
import argparse
import atexit
import signal

from subconvert.utils.Locale import _
from subconvert.utils.version import __appname__, __version__
from subconvert.cli import MainApp
from subconvert.gui import GuiApp
from subconvert.utils.PropertyFile import SubtitleProperties

from subconvert.parsing.Core import SubParser
from subconvert.parsing.Formats import *

log = logging.getLogger('Subconvert')

def cleanup(app):
    log.debug("Subconvert cleanup")
    app.cleanup()

def loadSpf(formats, filePath):
    try:
        spf = SubtitleProperties(formats, filePath)
    except FileNotFoundError:
        log.critical(_("No such file: '%s'") % filePath)
        sys.exit(2)
    return spf

def prepareOptions(subFormats):
    parser = argparse.ArgumentParser(
        description = _("Subconvert is a movie subtitles editor and converter."))

    parser.add_argument("files", metavar=_("FILE"), nargs="*", type = os.path.expanduser,
        help=_("files to open"))

    parser.add_argument("-c", "--console", action = "store_true",
        help = _("runs Subconvert in console"))
    parser.add_argument("-f", "--force", action = "store_true",
        help = _("forces all operations without asking (assuming yes)"))


    subtitleGroup = parser.add_argument_group(_("subtitle options"))
    subtitleGroup.add_argument("-o", "--output-file", metavar = _("FILE"), dest = "outputPath",
        type = os.path.expanduser,
        # Translators: Do not translate '%%f'
        help = _("output file. All occurences of '%%f', will be replaced by input file name base"))
    subtitleGroup.add_argument("-e", "--encoding", metavar = _("ENC"), dest = "inputEncoding",
        type = str,
        help = _("input file encoding"))
    subtitleGroup.add_argument("-E", "--reencode", metavar = _("ENC"), dest = "outputEncoding",
        type = str,
        help = _("changes output file encoding to ENC"))
    subtitleGroup.add_argument("-t", "--format", metavar = _("FMT"), dest = "outputFormat",
        type = str,
        help = _("sets output subtitle format to FMT"))
    subtitleGroup.add_argument("-p", "--property-file", metavar = _("FILE"), dest = "pfile",
        type = lambda filePath : loadSpf(subFormats, filePath),
        default = SubtitleProperties(subFormats),
        help = _("loads settings from spf (subtitle property file)"))
    subtitleGroup.add_argument("--sync", metavar = _("SPEC"), dest = "sync",
        type = str,
        help = _("synchronize subtitles according to SPEC"))

    movieGroup = parser.add_argument_group(_("video options"))
    movieGroup.add_argument("--fps", type = float,
        help = _("specifies video frames per second"))
    movieGroup.add_argument("-A", "--auto-fps", action = "store_true", dest = "autoFps",
        help = _("[DEPRECATED] uses MPlayer to automatically get FPS value from the video"))
    movieGroup.add_argument("-v", "--video", metavar = _("VIDEO"), type = os.path.expanduser,
        # Translators: Do not translate '%%f'
        help = _("specifies a video file to get FPS value from. "
            "All occurences of '%%f' will be replaced by input file name base"))

    miscGroup = parser.add_argument_group( _("miscellaneous options"))
    miscGroup.add_argument("--debug", action = "store_true",
        help = _("enables debug prints"))
    miscGroup.add_argument("--quiet", action = "store_true",
        help = _("silences Subconvert output"))
    miscGroup.add_argument("--version", action = "store_true",
        help = _("prints program version and exit"))

    return parser

def initSubParser():
    parser = SubParser()
    for Format in SubFormat.__subclasses__():
        parser.registerFormat(Format)
    return parser

def interruptHandler(signum, frame):
    sys.exit(1) # will spawn atexit

def startApp(args, parser):
    app = None
    if args.console:
        app = MainApp.SubApplication(args, parser)
    else:
        app = GuiApp.SubApplication(args, parser)

    atexit.register(cleanup, app)
    sys.exit(app.run())

def main():
    signal.signal(signal.SIGINT, interruptHandler)

    parser = initSubParser()
    optParser = prepareOptions(parser.formats)
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

    startApp(args, parser)
