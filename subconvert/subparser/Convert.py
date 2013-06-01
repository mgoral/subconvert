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
import gettext
import datetime

from subconvert.subparser import SubParser
from subconvert.subparser import FrameTime
from subconvert.subparser import Parsers

def acceptAlias(decoratedFunction):
    def wrapper(self, alias):
        key = alias
        if alias in self.aliases.keys():
            key = self.aliases[alias]
        return decoratedFunction(self, key)
    return wrapper

class SubConverterManager():
    """Manages SubConverter instances.

    SubConverters can be accessed via filePath or alias. Each alias is unique and is mapped to a
    single filePath (i.e. filePath might have several aliases but alias has only one filePath)."""

    def __init__(self):
        # { 'filepath' : SubConverter }
        self._converters = {}
        self.aliases = {}

    @acceptAlias
    def add(self, filePath):
        """Creates and returns a new converter if one with a given filePath doesn't exist yet.
        Returns existing one otherwise."""
        if not filePath in self._converters.keys():
            converter = SubConverter()
            self._converters[filePath] = converter
        return self._converters[filePath]

    @acceptAlias
    def get(self, filePath):
        return self._converters.get(filePath)

    @acceptAlias
    def remove(self, filePath):
        if filePath in self._converters.keys():
            del self._converters[filePath]

    def registerAlias(self, alias, filePath):
        self.aliases[alias] = filePath

    def deregisterAlias(self, alias):
        if alias in self.aliases.keys():
            del self.aliases[alias]

# TODO: maybe it'd be better to completely remove filePath dependency from SubConverter?
class SubConverter():
    def __init__(self):
        self._supportedParsers = SubParser.GenericSubParser.__subclasses__()
        self._movieFile = None
        self._fps = 25
        self._converter = None

        # Public attributes (don't want to write explicit getters for them
        self.parsedLines = []
        self.convertedLines = []

    def changeFps(self, fps):
        assert(fps > 0)

        self._fps = fps
        for subtitle in self.parsedLines:
            if subtitle is not None:
                subtitle['sub']['time_from'].changeFps(fps)
                subtitle['sub']['time_to'].changeFps(fps)
        return self

    # TODO: test
    def changeSubText(self, subNo, newText):
        self.sub(subNo)['text'] = newText
        return self

    # TODO: test
    def changeSubTimeFrom(self, subNo, newTime):
        self.sub(subNo)['time_from'] = newTime
        return self

    # TODO: test
    def changeSubTimeTo(self, subNo, newTime):
        self.sub(subNo)['time_to'] = newTime
        return self

    # TODO: test
    def increaseSubTime(self, subNo, newTime):
        sub = self.sub(subNo)
        sub['time_to'] = sub['time_to'] + newTime
        sub['time_from'] = sub['time_from'] + newTime
        return self

    # TODO: test
    def addSub(self, subNo, newSub):
        assert(len(self.parsedLines) > 0)
        if subNo > 0:
            if len(self.parsedLines) < subNo:
                self.parsedLines.append(newSub)
            else:
                self.parsedLines.insert(newSub)
                for i in range(subNo + 1, len(self.parsedLines)):
                    self.parsedLines[i]['sub_no'] += 1

    # TODO: test
    def removeSub(self, subNo):
        assert(subNo >= 0)
        assert(len(self.parsedLines) >= subNo)
        if subNo != len(self.parsedLines):
            for i in range(subNo, len(self.parsedLines)):
                self.parsedLines[i]['sub_no'] -= 1
        del self._converters[i]

    def fps(self):
        return self._fps

    def sub(self, subNo):
        assert(len(self.parsedLines) > 0)
        if self.parsedLines[subNo] is not None:
            return self.parsedLines[subNo]['sub']
        return None

    def parse(self, content):
        self.parsedLines = []
        self.convertedLines = []
        for supportedParser in self._supportedParsers:
            if not self.isParsed():
                parser = supportedParser(self._fps, content)
                parser.parse()
                self.parsedLines = parser.get_results()
        return self.parsedLines

    def isParsed(self):
        return len(self.parsedLines) > 0

    # TODO: test
    # TODO: SubConverter should accept somehow a full filepath to the new file. Only if it's not
    # provided, it should use the old one but with a new extension.
    def toFormat(self, newFormat):
        assert(self.parsedLines != [])

        self._converter = None
        for parser in self._supportedParsers:
            # Obtain user specified subclass
            if parser.__OPT__ == newFormat:
                self._converter = parser(self._fps)
                break

        assert(self._converter)

        # FIXME: This is crazy! I know that it works but it's too complicated! Refactor it!
        # Adding a header.
        subPair = [0, 0]
        for parsed in self.parsedLines:
            # FIXME: refactor the way that HEADER is stored and handled. It should be stored
            # independently to subtitles.
            if not subPair[1] and self._converter.__WITH_HEADER__: # Only the first element
                header = parsed['sub'].get('header')
                # FIXME: What is that?!
                if type(header) != dict:
                    header = {}
                header = self._converter.convert_header(header)
                if header:
                    try:
                        self.convertedLines.append(header)
                    except UnicodeEncodeError:
                        raise
            # FIXME: This is crazy! I know that it works but it's silly!
            # We actually parse subPair[0] but need subPair[1] (which is next subtitle) in case
            # there is not time_to.
            subPair[0] = subPair[1]
            subPair[1] = parsed
            try:
                if subPair[0]:
                    if not subPair[0]['sub']['time_to']:
                        if subPair[1] is None:
                            subPair[0]['sub']['time_to'] = \
                                subPair[0]['sub']['time_from'] + FrameTime.FrameTime(self._fps, seconds=2.5)
                        else:
                            subPair[0]['sub']['time_to'] = \
                                subPair[0]['sub']['time_from'] + (subPair[1]['sub']['time_from'] - subPair[0]['sub']['time_from']) * 0.85
                    sub = self._converter.convert(subPair[0])
                    try:
                        self.convertedLines.append(sub)
                    except UnicodeEncodeError:
                        raise
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
        return self.convertedLines

