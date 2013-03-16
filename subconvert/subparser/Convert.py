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


import os
import sys
import locale
import logging
import re
import gettext
import codecs
import datetime
import shutil
import encodings

from subprocess import Popen, PIPE

import subparser.SubParser as SubParser
import subparser.FrameTime as FrameTime
import subparser.Parsers as Parsers

try:
    import chardet
    IS_CHARDET = True
except ImportError:
    IS_CHARDET = False

log = logging.getLogger('subconvert.%s' % __name__)

class SubConverterManager():
    def __init__(self):
        self.converters = list()

    def add(self, converter):
        if converter not in self.converters:
            self.converters.append(converter)
            return True
        return False

    def get(self, filePath):
        for i, retConverter in enumerate(self.converters):
            if retConverter.getFilePath() == filePath:
                return retConverter
        return None

    def remove(self, filePath):
        for i, retConverter in enumerate(self.converters):
            if retConverter.getFilePath() == filePath:
                del self.converters[i]

class SubConverter():
    def __init__(self, filepath):
        self.supportedParsers = SubParser.GenericSubParser.__subclasses__()
        self.originalFilePath = filepath
        self.encoding = None
        self.movieFile = None
        self.fps = 25
        self.parsedLines = []
        self.convertedLines = []
        self.converter = None

        self.__detectOriginalEncoding()

    def __eq__(self, other):
        return self.originalFilePath == other.originalFilePath

    def __lt__(self, other):
        return self.originalFilePath < other.originalFilePath

    def __hash__(self):
        return hash(self.originalFilePath)

    #def __availableEncodings(self):
        # http://stackoverflow.com/questions/1707709/list-all-the-modules-that-are-part-of-a-python-package/1707786#1707786
    #    falsePositives = set(["aliases"])
    #    found = set(name for imp, name, ispkg in pkgutil.iter_modules(encodings.__path__) if not ispkg)
    #    found.difference_update(falsePositives)
    #    found = list(found)
    #    found.sort()
    #    return found

    def detectMovieFps(self, movieFile):
        """Fetch movie FPS from MPlayer output or return given default."""

        command = ['mplayer', '-really-quiet', '-vo', 'null', '-ao', 'null', '-frames', '0', '-identify',]
        command.append(movieFile)
        try:
            mpOut, mpErr = Popen(command, stdout=PIPE, stderr=PIPE).communicate()
            log.debug(mpOut)
            log.debug(mpErr)
            self.fps = re.search(r'ID_VIDEO_FPS=([\w/.]+)\s?', mpOut).group(1)
        except OSError:
            log.warning(_("Couldn't run mplayer. It has to be installed and placed in your $PATH in order to use auto_fps option."))
        except AttributeError:
            log.warning(_("Couldn't get FPS info from mplayer."))
        else:
            log.info(_("Got %s FPS from '%s'.") % (self.fps, movieFile))

    def __detectOriginalEncoding(self):
        """Try to detect file encoding
        'is' keyword checks objects identity and it's the key to disabling
        autodetect when '-e ascii' option is given. It seems that optparse
        creates a new object (which is logical) when given an option from
        shell and overrides a variable in program memory."""
        if IS_CHARDET:
            minimumConfidence = 0.52
            fileSize = os.path.getsize(self.originalFilePath)
            size = 5000 if fileSize > 5000 else fileSize
            with open(self.originalFilePath, mode='rb',) as file_:
                enc = chardet.detect(file_.read(size))
                log.debug(_("Detecting encoding from %d bytes") % size)
                log.debug(_(" ...chardet: %s") % enc)
            if enc['confidence'] > minimumConfidence:
                self.changeEncoding(enc['encoding'])
                log.debug(_(" ...detected %s encoding.") % enc['encoding'])
            else:
                log.info(_("I am not too confident about encoding (most probably %s). Setting \
                    default UTF-8") % enc['encoding'])
                self.changeEncoding('utf8')
        else:
            log.info(_("Chardet module is not installed on this system. \
                Setting default encoding (UTF-8)"))
            self.changeEncoding('utf8')

    def changeEncoding(self, encoding):
        # FIXME: check if a given encoding is available. The problem is that currently chardet
        # returns something line "utf-8" while available are "utf8" and "utf_8"...
        availableEncodings = (
            list(encodings.aliases.aliases.keys()) + list(encodings.aliases.aliases.values())
        )
        self.encoding = encoding
        return self

    def changeFps(self, fps):
        self.fps = fps
        return self

    def changeSubText(self, subNo, newText):
        self.getSub(subNo)['text'] = newText
        return self

    def changeSubTimeFrom(self, subNo, newTime):
        self.getSub(subNo)['time_from'] = newTime
        return self

    def changeSubTimeTo(self, subNo, newTime):
        self.getSub(subNo)['time_to'] = newTime
        return self

    def increaseSubTime(self, subNo, newTime):
        sub = self.getSub(subNo)
        sub['time_to'] = sub['time_to'] + newTime
        sub['time_from'] = sub['time_from'] + newTime
        return self

    def getEncoding(self):
        return self.encoding

    def getFps(self):
        return self.fps

    def getSub(self, subNo):
        assert(len(self.parsedLines) > 0)
        return self.parsedLines[subNo]['sub']

    def getFilePath(self):
        return self.originalFilePath

    #def backup(self, filename):
    #    """Backup a file to filename_strftime (by moving it, not copying).
    #    Return a tuple (backed_up_filename, old_filename)"""
    #
    #    new_arg = ''.join([filename, datetime.datetime.now().strftime('_%y%m%d%H%M%S')])
    #    try:
    #        os.remove(new_arg)
    #        log.debug(_("'%s' exists and needs to be removed before backing up.") %
    #            new_arg.encode(locale.getpreferredencoding()))
    #    except OSError:
    #        pass
    #    shutil.move(filename, new_arg)
    #    return (new_arg, filename)

    #def save(self, newFileName=None):
    #    assert(self.parsedLines != [])
    #
    #    if newFileName is None:
    #        assert(self.converter is not None)
    #        fileName, extension = os.path.splitext(self.originalFilePath)
    #        destinationFile = fileName + '.' + self.converter.__EXT__
    #    else:
    #        destinationFile = newFileName

    def parse(self):
        try:
            with codecs.open(self.originalFilePath, mode='r', encoding=self.encoding) as file_:
                fileInput = file_.readlines()
        except LookupError as msg:
            raise LookupError(_("Unknown encoding name: '%s'.") % file_encoding)

        log.info(_("Trying to parse %s...") % self.originalFilePath)
        for supportedParser in self.supportedParsers:
            if not self.parsedLines:
                parser = supportedParser(self.originalFilePath, self.fps, self.encoding, fileInput)
                parser.parse()
                self.parsedLines = parser.get_results()

    def toFormat(self, newFormat, encoding=None):
        assert(self.parsedLines != [])

        if encoding is None:
            encoding = self.encoding

        for parser in self.supportedParsers:
            # Obtain user specified subclass
            if parser.__OPT__ == newFormat:
                filename, _notUsed = os.path.splitext(self.originalFilePath)
                self.converter = parser(filename + '.' + parser.__EXT__, self.fps, encoding)
                break
        if self.converter.__OPT__ != newFormat:
            raise NameError

        subPair = [0, 0]
        for parsed in self.parsedLines:
            if not subPair[1] and self.converter.__WITH_HEADER__: # Only the first element
                header = parsed['sub'].get('header')
                if type(header) != dict:
                    header = {}
                header = self.converter.convert_header(header)
                if header:
                    try:
                        self.convertedLines.append(header)
                    except UnicodeEncodeError:
                        raise
            subPair[0] = subPair[1]
            subPair[1] = parsed
            try:
                if subPair[0]:
                    if not subPair[0]['sub']['time_to']:
                        if subPair[1] is None:
                            subPair[0]['sub']['time_to'] = \
                                subPair[0]['sub']['time_from'] + FrameTime.FrameTime(self.fps, 'full_seconds', seconds = 2.5)
                        else:
                            subPair[0]['sub']['time_to'] = \
                                subPair[0]['sub']['time_from'] + \
                                (subPair[1]['sub']['time_from'] - subPair[0]['sub']['time_from']) * 0.85
                    sub = self.converter.convert(subPair[0])
                    try:
                        self.convertedLines.append(sub)
                    except UnicodeEncodeError:
                        raise
            except AssertionError:
                log.warning(_("Correct time not asserted for subtitle %d. Skipping it...") % (subPair[0]['sub_no']))
                log.debug(_(".. incorrect subtitle pair times: (%s, %s)") % (subPair[0]['sub']['time_from'], subPair[1]['sub']['time_from']))
        return self.convertedLines

