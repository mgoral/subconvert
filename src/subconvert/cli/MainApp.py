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

import sys
import re
import logging
from string import Template

from subconvert.parsing.Core import SubConverter, SubParsingError
from subconvert.parsing.Formats import *
from subconvert.parsing.Offset import TimeSync
from subconvert.utils.Locale import _
from subconvert.utils.SubtitleData import SubtitleData
from subconvert.utils.SubFile import File
from subconvert.utils.SubSettings import SubSettings
from subconvert.utils.Encodings import ALL_ENCODINGS
from subconvert.utils.PropertyFile import SubtitleProperties

import subconvert.cli.syncparse as syncparse

from subconvert.utils.SubException import SubException

log = logging.getLogger('Subconvert.%s' % __name__)

class FileTemplate(Template):
        delimiter = '%'

class SubApplication:
    def __init__(self, args, parser):
        self._args = args
        self._parser = parser

    def cleanup(self):
        pass

    def parseFile(self, subFile, inputEncoding , fps):
        content = subFile.read(inputEncoding)
        try:
            subtitles = self._parser.parse(content, fps)
        except SubParsingError as msg:
            log.error(msg)
            raise SubException(_("Couldn't parse file '%s'" % subFile.path))

        return subtitles

    def getFps(self, subFile):
        fps = self._args.fps
        if fps is None:
            fps = self._args.pfile.fps # default value
            if self._args.pfile.autoFps:
                movieFile = self._parsePathTemplate(self._args.video, subFile.path)
                videoInfo = subFile.detectFps(movieFile, fps)
                fps = videoInfo.fps
        return fps

    def updateEncodings(self, subFile):
        self._inputEncoding = self._args.inputEncoding
        self._outputEncoding = self._args.outputEncoding

        if self._inputEncoding is None:
            self._inputEncoding = subFile.detectEncoding()

        if self._outputEncoding is None:
            self._outputEncoding = self._inputEncoding

    def getOutputFormat(self):
        if self._args.outputFormat is not None:
            formats = self._parser.formats
            for fmt in formats:
                if fmt.OPT == self._args.outputFormat.lower():
                    return fmt
            raise SubException(_("Unknown output format: '%s'") % self._args.outputFormat)
        elif self._args.pfile.outputFormat.NAME != SubFormat.NAME: # fmt != 'Generic'
            return self._args.pfile.outputFormat
        return SubRip

    def getInputEncoding(self, subFile):
        inputEncoding = self._args.inputEncoding
        if inputEncoding is None:
            if self._args.pfile.autoInputEncoding is False:
                inputEncoding = self._args.pfile.inputEncoding
            else:
                inputEncoding = subFile.detectEncoding()
        return self._checkEncoding(inputEncoding.lower())

    def getOutputEncoding(self, default):
        outputEncoding = self._args.outputEncoding
        if outputEncoding is None:
            if self._args.pfile.changeEncoding is True:
                outputEncoding = self._args.pfile.outputEncoding
            else:
                outputEncoding = default
        return self._checkEncoding(outputEncoding.lower())

    def getOutputFilePath(self, subFile, formatExtension):
        outputPath = self._parsePathTemplate(self._args.outputPath, subFile.path)
        if outputPath is None:
            filename = os.path.splitext(subFile.path)[0]
            outputPath = '.'.join((filename, formatExtension))
        return outputPath

    def writeSubtitles(self, convertedSubtitles, filePath, encoding):
        try:
            file_ = File(filePath)
        except:
            # File doesn't exist, we can safely write to it
            File.write(filePath, convertedSubtitles, encoding)
            log.info(_("File %s saved.") % filePath)
        else:
            # A little hack to ensure that translator won't make a mistake
            choices = { 'yes': _('y'), 'no': _('n'), 'quit': _('q'), 'backup': _('b') }
            choice = ''

            if self._args.force:
                choice = choices["yes"]
            while(choice not in choices.values()):
                vals = {
                    "file": filePath, "yes": choices["yes"], "no": choices['no'],
                    "bck": choices['backup'], "quit": choices["quit"]
                }

                choice = input(
                    _("File '%(file)s' exists. Overwrite? [%(yes)s/%(no)s/%(bck)s/%(quit)s]") % 
                    vals)

            if choice == choices['backup']:
                backupFilePath = file_.backup()
                log.info(_("Backup: %s") % backupFilePath)
                log.info(_("Overwriting %s") % filePath)
                file_.overwrite(convertedSubtitles, encoding)
            elif choice == choices['no']:
                log.info(_("Skipping %s") % filePath)
                return
            elif choice == choices['yes']:
                log.info(_("Overwriting %s") % filePath)
                file_.overwrite(convertedSubtitles, encoding)
            elif choice == choices['quit']:
                log.info(_("Quitting converting work."))
                sys.exit(0)

    def run(self):
        try:
            outputFormat = self.getOutputFormat()
            converter = SubConverter()

            if len(self._args.files) == 0:
                log.warning(_("No files selected."))

            if self._args.autoFps:
                log.warning(_("-A, --auto-fps switches are deprecated."))
                log.warning(_("  note: FPS is now automatically fetched whenever it's suitable."))

            for filePath in self._args.files:
                log.info(_("Starting a job for file: %s") % filePath)
                try:
                    subFile = File(filePath)
                except IOError:
                    log.warning( _("File '%s' doesn't exist. Skipping...") % filePath)
                    continue

                data = self.createSubData(subFile, outputFormat)

                if data is not None:
                    convertedSubtitles = converter.convert(data.outputFormat, data.subtitles)
                    outputFilePath = self.getOutputFilePath(subFile, data.outputFormat.EXTENSION)
                    self.writeSubtitles(convertedSubtitles, outputFilePath, data.outputEncoding)

        except SubException as msg:
            log.debug(_("Unhandled Subconvert exception occured:"))
            log.critical(str(msg))
            return 127

        return 0

    def printData(self, filePath, data):
        log.debug(_("File properties for %s:") % filePath)
        log.debug(_("FPS             : %s") % data.fps)
        log.debug(_("Input encoding  : %s") % data.inputEncoding)
        log.debug(_("Output encoding : %s") % data.outputEncoding)
        log.debug(_("Output format   : %s") % data.outputFormat.NAME)

    def createSubData(self, subFile, outputFormat):
        data = SubtitleData()
        data.fps = self.getFps(subFile)
        data.outputFormat = outputFormat
        data.inputEncoding = self.getInputEncoding(subFile)
        data.outputEncoding = self.getOutputEncoding(data.inputEncoding)

        self.printData(subFile.path, data)

        try:
            data.subtitles = self.parseFile(subFile, data.inputEncoding, data.fps)
            if self._args.sync:
                syncpoints = syncparse.parse(self._args.sync, data.subtitles)
                ts = TimeSync(data.subtitles)
                ts.sync(syncpoints)
        except SubException as msg:
            log.error(str(msg))
            return None

        # shouldn't throw as all common checks are performed by getters
        data.verifyAll()
        return data

    def _checkEncoding(self, encoding):
        if encoding not in ALL_ENCODINGS:
            raise SubException(_("Incorrect encoding: '%s'") % encoding)
        return encoding

    def _parsePathTemplate(self, template, filePath):
        if template is not None:
            path, extension = os.path.splitext(filePath)
            filename = os.path.basename(path)
            dirname = os.path.dirname(path)
            if extension.startswith('.'): # might be an empty string as well
                extension = extension[1:]
            s = FileTemplate(template)
            return s.substitute(f = filename, e = extension)
        return None
