"""
Copyright (C) 2013 Michal Goral.

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

import pickle
from subconvert.parsing.Formats import *

def loadPropertyFile(filePath):
    with open(filePath, 'rb') as f:
        obj = pickle.load(f)
    return obj

def savePropertyFile(filePath, obj):
    with open(filePath, 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

class SubtitleProperties:
    def __init__(self):
        self._autoFps = False
        self._fps = 25.0
        self._inputEncoding = None
        self._outputEncoding = None
        self._changeEncoding = False
        self._outputFormat = SubFormat

    @property
    def autoFps(self):
        return self._autoFps

    @autoFps.setter
    def autoFps(self, val):
        if val not in (True, False):
            raise TypeError("Expected boolean!")
        self._autoFps = bool(val)

    @property
    def fps(self):
        return self._fps

    @fps.setter
    def fps(self, val):
        self._fps = float(val)

    @property
    def inputEncoding(self):
        return self._inputEncoding

    @inputEncoding.setter
    def inputEncoding(self, val):
        if val is None:
            self._inputEncoding = val
        else:
            self._inputEncoding = str(val)

    @property
    def outputEncoding(self):
        return self._outputEncoding

    @outputEncoding.setter
    def outputEncoding(self, val):
        if val is None:
            self._outputEncoding = val
        else:
            self._outputEncoding = str(val)

    @property
    def changeEncoding(self):
        return self._changeEncoding

    @changeEncoding.setter
    def changeEncoding(self, val):
        if val not in (True, False):
            raise TypeError("Expected boolean!")
        self._changeEncoding = bool(val)

    @property
    def outputFormat(self):
        return self._outputFormat

    @outputFormat.setter
    def outputFormat(self, val):
        if not issubclass(val, SubFormat):
            raise TypeError("Incorrect outputFormat type!")
        self._outputFormat = val

