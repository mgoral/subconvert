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

# Unfortunately unittest.mock is available in std from Python 3.3 and I don't want to create
# another dependency

class FrameTimeMock:
    def __init__(self, fps):
        self.fps = fps
        self._fps = fps
        self._full_seconds = 0

    def __eq__(self, other):
        return self.fps == other.fps

    def __ne__(self, other):
        return self.fps != other.fps

    def __add__(self, other):
        return FrameTimeMock(self.fps)

    def __sub__(self, other):
        return FrameTimeMock(self.fps)

    def __mul__(self, val):
        return FrameTimeMock(self.fps)

class SubtitleMock:
    def __init__(self, start = None, end = None, text = None):
        self.start = start
        self.end = end
        self.text = text
        self.fps = start.fps if start is not None else None

    def __eq__(self, other):
        return self.text == other.text

    def __ne__(self, other):
        return self.text != other.text

    def change(self, start = None, end = None, text = None):
        if start is not None:
            self.start = start
        if end is not None:
            self.end = end
        if text is not None:
            self.text = text
