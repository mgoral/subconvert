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

from subconvert.parsing.Core import SubManager
from subconvert.parsing.Formats import *
from subconvert.utils.Encodings import ALL_ENCODINGS

class SubtitleData:
    subtitles = None
    fps = None
    outputFormat = None
    inputEncoding = None
    outputEncoding = None
    videoPath = None

    def clone(self):
        other = SubtitleData()
        if self.subtitles is not None:
            other.subtitles = self.subtitles.clone()
        else:
            other.subtitles = self.subtitles
        other.fps = self.fps
        other.outputFormat = self.outputFormat
        other.inputEncoding = self.inputEncoding
        other.outputEncoding = self.outputEncoding
        other.videoPath = self.videoPath
        return other

    def empty(self):
        return (
            self.subtitles is None and
            self.fps is None and
            self.outputFormat is None and
            self.inputEncoding is None and
            self.outputEncoding is None and
            self.videoPath is None
        )

    def encode(self, encoding):
        subtitles = self.subtitles.clone()
        encoding = encoding.lower()
        for i, subtitle in enumerate(subtitles):
            encodedBits = subtitle.text.encode(self.inputEncoding)
            subtitles.changeSubText(i, encodedBits.decode(encoding))
        self.inputEncoding = encoding
        self.subtitles = subtitles

    def verifySubtitles(self):
        if self.subtitles is None:
            raise TypeError("Subtitles cannot be of type 'NoneType'!")
        if type(self.subtitles) is not SubManager:
            raise TypeError(_("Subtitles are not of type 'SubManager'!"))

    def verifyFps(self):
        if not isinstance(self.fps, float):
            raise TypeError("FPS value is not a float!")

    def verifyOutputFormat(self):
        if self.outputFormat is None:
            raise TypeError("Output format cannot be of type 'NoneType'!")
        if not issubclass(self.outputFormat, SubFormat):
            raise TypeError("Output format is not of type 'SubFormat'!")

    def verifyInputEncoding(self):
        if self.inputEncoding is None:
            raise TypeError("Input encoding cannot be of type 'NoneType'!")
        if not isinstance(self.inputEncoding, str):
            raise TypeError("Input encoding is not a string!")
        if self.inputEncoding not in ALL_ENCODINGS:
            raise ValueError("Input encoding is not a supported encoding!")

    def verifyOutputEncoding(self):
        if self.outputEncoding is None:
            raise TypeError("Output encoding cannot be of type 'NoneType'!")
        if not isinstance(self.outputEncoding, str):
            raise TypeError("Output encoding is not a string!")
        if self.outputEncoding not in ALL_ENCODINGS:
            raise ValueError("Output encoding is not a supported encoding!")

    def verifyAll(self):
        self.verifySubtitles()
        self.verifyFps()
        self.verifyOutputFormat()
        self.verifyInputEncoding()
        self.verifyOutputEncoding()
