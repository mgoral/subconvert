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
import locale
import gettext
import re
import codecs

from subconvert.parsing.FrameTime import FrameTime
from subconvert.utils.Alias import *

class Subtitle():
    def __init__(self, start = None, end = None, text = None):
        self.__start = start
        self.__end = end
        self.__text = text

    def start(self):
        return self.__start

    def end(self):
        return self.__end

    def text(self):
        return self.__text

    def change(self, start = None, end = None, text = None):
        if start is not None:
            self.__start = start
        if end is not None:
            self.__end = end
        if text is not None:
            self.__text = text

    def isEmpty(self):
        return self.__start or self.__end or self.__text

class Header(AliasBase):
    def __init__(self):
        super(Header, self).__init__()
        self.__entries = {}

    @acceptAlias
    def add(self, entry, value):
        self.__entries[entry] = value

    @acceptAlias
    def erase(self, entry):
        if entry in self.__entries.keys():
            del self.__entries[entry]

    @acceptAlias
    def get(self, entry, default=None):
        return self.__entries.get(entry, default)

    def empty(self):
        return len(self.__entries) == 0

    def clear(self):
        self.__entries.clear()

class SubParsingError(Exception):
    '''Custom parsing error class.'''
    def __init__(self, message, lineNo):
        Exception.__init__(self, message)
        self.lineNo = lineNo

class SubManager:
    def __init__(self):
        self._subs = []
        self._header = Header()

    def insert(self, subNo, newSub):
        if subNo > 0:
            if len(self._subs) < subNo:
                self.append(newSub)
            else:
                if sub.end() is None:
                    endTime = self._subs[subNo].start() + \
                        (self._subs[subNo + 1].start() - self._subs[subNo].start()) * 0.85
                    sub.change(end = endTime)
                self._subs.insert(subNo, newSub)

    def append(self, sub):
        if sub.end() is None:
            fps = sub.start().fps()
            endTime = sub.start() + FrameTime(fps, seconds = 2.5)
            sub.change(end = endTime)
        self._subs.append(sub)

    # TODO: test
    def remove(self, subNo):
        del self._subs[subNo]

    def clear(self):
        self._subs = []

    def changeFps(self, fps):
        if not fps > 0:
            raise ValueError

        for sub in self._subs:
            sub.start().changeFps(fps)
            sub.end().changeFps(fps)
        return self

    # TODO: test
    def changeSubText(self, subNo, newText):
        self._subs(subNo).change(text = newText)
        return self

    # TODO: test
    def changeSubStart(self, subNo, newTime):
        self._subs(subNo).change(start = newTime)
        return self

    # TODO: test
    def changeSubEnd(self, subNo, newTime):
        self._subs(subNo).change(end = newTime)
        return self

    def header(self):
        return self._header

    def size(self):
        return len(self._subs)

    def __eq__(self, other):
        return self._subs == other._subs

    def __ne__(self, other):
        return self._subs == other._subs

    def __lt__(self, other):
        return self._subs < other._subs

    def __gt__(self, other):
        return self._subs > other._subs

    # Do not implement __setitem__ as we want to keep explicit control over things that are added
    def __getitem__(self, key):
        return self._subs[key]

    def __iter__(self):
        for sub in self._subs:
            yield sub

class SubParser:
    def __init__(self):
        self._maxHeaderLen = 50
        self._maxFmtSearch = 35
        self._formatFound= False
        self._headerFound = False

        self._SupportedFormats = set()

        self._subtitles = SubManager()

    def message(self, lineNo, msg = "parsing error."):
        '''Uniform error message.'''
        return _("%d: %s") % (lineNo + 1, msg)

    # TODO: parser should not be aware of the encoding
    def _initialLinePrepare(self, line, lineNo):
        if lineNo == 0 and line.startswith( codecs.BOM_UTF8.decode("utf8") ):
            line = line[1:]
        return line

    def registerFormat(self, fmt):
        self._SupportedFormats.add(fmt)

    # TODO: implementation (return a list of format names)
    # TODO: test
    def formats(self):
        pass

    def isParsed(self):
        return self._formatFound

    def parse(self, content, fps = 25):
        self._subtitles.clear()
        self._formatFound = False
        for Format in self._SupportedFormats:
            if not self._formatFound:
                subFormat = Format()
                try:
                    self.__parseFormat(subFormat, content, fps)
                except SubParsingError:
                    self._subtitles.clear()
                    raise
        return self._subtitles

    def __parseFormat(self, fmt, content, fps = 25):
        '''Actual parser. Please note that time_to is not required to process as not all subtitles
        provide it.'''

        subSection = ''
        for lineNo, line in enumerate(content):
            line = self._initialLinePrepare(line, lineNo)
            if not fmt.WITH_HEADER and not self._formatFound and lineNo > self._maxFmtSearch:
                return

            subSection = ''.join([subSection, line])
            if fmt.WITH_HEADER and not self._headerFound:
                if lineNo > self._maxHeaderLen:
                    return
                self._headerFound = fmt.addHeaderInfo(subSection, self._subtitles.header())
                if self._headerFound:
                    self._formatFound = True
                    subSection = ''
            elif fmt.subtitleEnds(line) or (lineNo + 1) == len(content):
                subtitle = fmt.createSubtitle(fps, subSection)
                if subtitle is None:
                    if subSection in ('\n', '\r\n', '\r'):
                        subSection = ''
                        continue
                    elif self._subtitles.size() > 0:
                        raise SubParsingError(_("%s parsing error.") % self.NAME, lineNo)
                    else:
                        return

                # store parsing result if new end marker occurred, then clear results
                if subtitle.start() and subtitle.text():
                    self._formatFound = True
                    self._subtitles.append(subtitle)
                elif subtitle.start() and not subtitle.text():
                    pass
                else:
                    return
                subSection = ''

    def getResults(self):
        '''Return parsing results which is a list of dictionaries'''
        return self._subtitles

class SubConverter():
    def __init__(self):
        self.convertedLines = []

    # TODO: test
    def convert(self, Format, subtitles):
        assert(subtitles.size() != 0)

        fmt = Format()

        if fmt.WITH_HEADER:
            head = fmt.convertHeader(subtitles.header())
            self.convertedLines.append(head)

        for subNo, sub in enumerate(subtitles):
            if sub is not None:
                try:
                    subText = sub.text().format(**fmt.formatting)
                except KeyError:
                    subText = sub.text()
                try:
                    convertedSub = fmt.subFormat.format(gsp_no = subNo, \
                        gsp_from = fmt.convertTime(sub.start(), 'time_from'), \
                        gsp_to = fmt.convertTime(sub.end(), 'time_to'), \
                        gsp_text = subText)
                except AssertionError:
                    # TODO: handle it somehow. Maybe inform SubConverter client about situation. Maybe
                    # create a list of tuples where second element would be a sub and first element
                    # would be flag indicating whether it's correct (it it's not, then the second
                    # element would contain unconverted sub)
                    pass
                    # TODO: logs are left as info source about this assertion. Remove when it'll be
                    # handled properly.
                    #log.warning(_("Correct time not asserted for subtitle %d. Skipping it...") % (subPair[0]['sub_no']))
                    #log.debug(_(".. incorrect subtitle pair times: (%s, %s)") % (subPair[0]['sub']['time_from'], subPair[1]['sub']['time_from']))
                self.convertedLines.append(convertedSub)
        return self.convertedLines

