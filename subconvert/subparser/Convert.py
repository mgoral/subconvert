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
import logging
import gettext
import datetime

import subparser.SubParser as SubParser
import subparser.FrameTime as FrameTime
import subparser.Parsers as Parsers

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
        self.movieFile = None
        self.fps = 25
        self.parsedLines = []
        self.convertedLines = []
        self.converter = None

    def __eq__(self, other):
        return self.originalFilePath == other.originalFilePath

    def __lt__(self, other):
        return self.originalFilePath < other.originalFilePath

    def __hash__(self):
        return hash(self.originalFilePath)


    def changeFps(self, fps):
        assert(fps > 0)

        self.fps = fps
        for subtitle in self.parsedLines:
            subtitle['sub']['time_from'].changeFps(fps)
            subtitle['sub']['time_to'].changeFps(fps)
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

    def addSub(self, subNo, newSub):
        assert(len(self.parsedLines) > 0)
        if subNo > 0:
            if len(self.parsedLines) < subNo:
                log.warning(_("There are only %d subtitles. Pushing new one to the end."))
                self.parsedLines.append(newSub)
            else:
                self.parsedLines.insert(newSub)
                for i in range(subNo + 1, len(self.parsedLines)):
                    self.parsedLines[i]['sub_no'] += 1

    def removeSub(self, subNo):
        assert(subNo > 0)
        assert(len(self.parsedLines) >= subNo)
        if subNo != len(self.parsedLines):
            for i in range(subNo, len(self.parsedLines)):
                self.parsedLines[i]['sub_no'] -= 1
        del self.converters[i]

    def getFps(self):
        return self.fps

    def getSub(self, subNo):
        assert(len(self.parsedLines) > 0)
        return self.parsedLines[subNo]['sub']

    def getFilePath(self):
        return self.originalFilePath

    def parse(self, content):
        log.info(_("Trying to parse %s...") % self.originalFilePath)
        self.parsedLines = []
        self.convertedLines = []
        for supportedParser in self.supportedParsers:
            if not self.parsedLines:
                parser = supportedParser(self.originalFilePath, self.fps, content)
                parser.parse()
                self.parsedLines = parser.get_results()

    def toFormat(self, newFormat):
        assert(self.parsedLines != [])

        for parser in self.supportedParsers:
            # Obtain user specified subclass
            if parser.__OPT__ == newFormat:
                filename, _notUsed = os.path.splitext(self.originalFilePath)
                self.converter = parser(filename + '.' + parser.__EXT__, self.fps)
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

