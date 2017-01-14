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
import re
import codecs

from subconvert.parsing.FrameTime import FrameTime
from subconvert.utils.Locale import _
from subconvert.utils.SubException import SubException, SubAssert
from subconvert.utils.Alias import *

#TODO: add comparing Subtitles (i.e. __eq__, __ne__ etc.)
class Subtitle():
    def __init__(self, start = None, end = None, text = None):
        self._start = None
        self._end = None
        self._text = None
        self.change(start, end, text)

    def _validateFps(self, start, end):
        startFps = None
        endFps = None
        if start and end:
            startFps = start.fps
            endFps = end.fps
        elif end and self._start:
            startFps = self._start.fps
            endFps = end.fps
        elif start and self._end:
            startFps = start.fps
            endFps = self._end.fps

        if startFps != endFps:
            raise ValueError("Subtitle FPS values differ: %s != %s" % (startFps, endFps))

    def clone(self):
        other = Subtitle()
        other._start = self._start.clone()
        other._end = self._end.clone()
        other._text = self._text
        return other

    @property
    def start(self):
        return self._start

    @property
    def end(self):
        return self._end

    @property
    def text(self):
        return self._text

    @property
    def fps(self):
        if self._start:
            return self._start.fps
        return None

    @fps.setter
    def fps(self, value):
        if self._start:
            self._start.fps = value
        if self._end:
            self._end.fps = value

    def change(self, start = None, end = None, text = None):
        self._validateFps(start, end)
        if start is not None:
            self._start = start
        if end is not None:
            self._end = end
        if text is not None:
            self._text = text

    def empty(self):
        return not (bool(self._start) or bool(self._end) or bool(self._text))

class Header(AliasBase):
    def __init__(self):
        super(Header, self).__init__()
        self._entries = {}

    def clone(self):
        other = Header()
        other._aliases = self._aliases.copy()
        other._entries = self._entries.copy()
        return other

    @acceptAlias
    def add(self, entry, value):
        self._entries[entry] = value

    @acceptAlias
    def erase(self, entry):
        if entry in self._entries.keys():
            del self._entries[entry]

    @acceptAlias
    def get(self, entry, default=None):
        return self._entries.get(entry, default)

    def empty(self):
        return len(self._entries) == 0

    def clear(self):
        self._entries.clear()

class SubParsingError(SubException):
    '''Custom parsing error class.'''
    def __init__(self, message, lineNo):
        super().__init__("%d: %s" % (lineNo, message))
        self.lineNo = lineNo

class SubManager:
    def __init__(self):
        self._subs = []
        self._header = Header()

        # if sub has been appended without endTime, its auto endTime should be changed once when a
        # new sub is appended again
        self._invalidTime = False

    def _autoSetEnd(self, sub, nextSub = None):
        endTime = None
        if nextSub is None:
            endTime = sub.start + FrameTime(sub.fps, seconds = 2.5)
        else:
            endTime = sub.start + (nextSub.start - sub.start) * 0.85
        sub.change(end = endTime)

    def clone(self):
        other = SubManager()
        other._header = self._header.clone()
        other._invalidTime = self._invalidTime
        other._subs = []
        for sub in self._subs:
            other._subs.append(sub.clone())
        return other

    def insert(self, subNo, sub):
        if subNo >= 0:
            if len(self._subs) < subNo:
                self.append(sub)
            else:
                if sub.end is None:
                    self._autoSetEnd(sub, self._subs[subNo + 1])
                self._subs.insert(subNo, sub)
        else:
            raise ValueError("insert only accepts positive indices")

    def append(self, sub):
        if self._invalidTime:
            invalidSub = self._subs[-1]
            self._autoSetEnd(invalidSub, sub)
            self._invalidTime = False

        if sub.end is None:
            self._autoSetEnd(sub)
            self._invalidTime = True
        self._subs.append(sub)

    # TODO: test
    def remove(self, subNo):
        if subNo == self.size() - 1:
            self._invalidTime = False
        del self._subs[subNo]

    def clear(self):
        self._subs = []
        self._invalidTime = False

    # TODO: test
    @property
    def fps(self):
        if self.size() > 0:
            return self._subs[0].fps
        return None

    def changeFps(self, fps):
        if not fps > 0:
            raise ValueError("Incorrect FPS value")

        for sub in self._subs:
            sub.fps = fps
        return self

    # TODO: test
    def changeSubText(self, subNo, newText):
        self._subs[subNo].change(text = newText)
        return self

    # TODO: test
    def changeSubStart(self, subNo, newTime):
        self._subs[subNo].change(start = newTime)
        return self

    # TODO: test
    def changeSubEnd(self, subNo, newTime):
        self._subs[subNo].change(end = newTime)
        if subNo == self.size() - 1:
            self._invalidTime = False
        return self

    # TODO: test
    def offset(self, ft):
        for sub in self._subs:
            sub.change(start=sub.start + ft, end=sub.end + ft)

    def header(self):
        return self._header

    def size(self):
        return len(self._subs)

    def __eq__(self, other):
        return self._subs == other._subs

    def __ne__(self, other):
        return self._subs != other._subs

    def __lt__(self, other):
        return self._subs < other._subs

    def __gt__(self, other):
        return self._subs > other._subs

    # Do not implement __setitem__ as we want to keep explicit control over things that are added
    def __getitem__(self, key):
        return self._subs[key].clone()

    def __iter__(self):
        for sub in self._subs:
            yield sub.clone()

    def __len__(self):
        return len(self._subs)

class SubParser:
    def __init__(self):
        self._maxHeaderLen = 50
        self._maxFmtSearch = 35
        self._formatFound= False

        self._supportedFormats = set()

        self._subtitles = SubManager()
        self._format = None

    def message(self, lineNo, msg = "parsing error."):
        '''Uniform error message.'''
        return "%d: %s" % (lineNo + 1, msg)

    # TODO: parser should not be aware of the encoding
    def _initialLinePrepare(self, line, lineNo):
        if lineNo == 0 and line.startswith( codecs.BOM_UTF8.decode("utf8") ):
            line = line[1:]
        return line

    def registerFormat(self, fmt):
        self._supportedFormats.add(fmt)

    # TODO: test
    @property
    def formats(self):
        return frozenset(self._supportedFormats)

    # It is not a @property, because calling parser.parsedFormat() by accident would actually
    # return a created instance of SubFormat (i.e. would result in a SubFormat())
    def parsedFormat(self):
        if self._formatFound:
            return self._format
        return None

    def parse(self, content, fps = 25):
        # return a new object each time (otherwise it'd contantly modify the same reference
        self._subtitles = SubManager()
        self._formatFound = False
        for Format in self._supportedFormats:
            if not self._formatFound:
                subFormat = Format()
                self._format = Format
                try:
                    self.__parseFormat(subFormat, content, fps)
                except SubParsingError:
                    self._subtitles.clear()
                    raise
        if self._subtitles.size() == 0:
            raise SubParsingError(_("Not a known subtitle format"), 0)
        return self._subtitles

    def __parseFormat(self, fmt, content, fps = 25):
        '''Actual parser. Please note that time_to is not required to process as not all subtitles
        provide it.'''

        headerFound = False
        subSection = ''
        for lineNo, line in enumerate(content):
            line = self._initialLinePrepare(line, lineNo)
            if not fmt.WITH_HEADER and not self._formatFound and lineNo > self._maxFmtSearch:
                return

            subSection = ''.join([subSection, line])
            if fmt.WITH_HEADER and not headerFound:
                if lineNo > self._maxHeaderLen:
                    return
                headerFound = fmt.addHeaderInfo(subSection, self._subtitles.header())
                if headerFound:
                    self._formatFound = True
                    subSection = ''
            elif fmt.subtitleEnds(line) or (lineNo + 1) == len(content):
                subtitle = fmt.createSubtitle(fps, subSection)
                if subtitle is None:
                    if subSection in ('\n', '\r\n', '\r'):
                        subSection = ''
                        continue
                    elif self._subtitles.size() > 0:
                        raise SubParsingError(_("Parsing error"), lineNo)
                    else:
                        return

                # store parsing result if new end marker occurred, then clear results
                if subtitle.start and subtitle.text:
                    self._formatFound = True
                    try:
                        self._subtitles.append(subtitle)
                    except SubException as msg:
                        raise SubParsingError(msg, lineNo)
                elif subtitle.start and not subtitle.text:
                    pass
                else:
                    return
                subSection = ''

    @property
    def results(self):
        '''Return parsing results which is a list of dictionaries'''
        return self._subtitles

class SubConverter:
    # TODO: test
    def convert(self, Format, subtitles):
        fmt = Format()
        convertedLines = []

        if fmt.WITH_HEADER:
            head = fmt.convertHeader(subtitles.header())
            convertedLines.append(head)

        for subNo, sub in enumerate(subtitles):
            if sub is not None: # FIXME: do we have to check it?
                try:
                    subText = sub.text.format(**fmt.formatting)
                except KeyError:
                    subText = sub.text
                subText = subText.strip() # unnecessary whitespaces will probably break subtitles
                convertedSub = fmt.subFormatTemplate.format(gsp_no = subNo, \
                    gsp_from = fmt.convertTime(sub.start, 'time_from'), \
                    gsp_to = fmt.convertTime(sub.end, 'time_to'), \
                    gsp_text = subText)
                convertedLines.append(convertedSub)
        return convertedLines

